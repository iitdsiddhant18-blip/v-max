"""Real local Phase 4 matrix. Evaluation topics never enter production policy."""
import argparse,hashlib,json,os,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app.schema import GenerateRequest
from backend.app.live import plan_timed_lesson,prepare_lesson
from backend.app.planner import post_to_local_ollama,ALLOWED_MODELS
from backend.app.visual_planner import plan_visual
from backend.app.visual_schema import VisualPlan
from backend.app.visual_validate import validate_plan
from backend.app.lesson_complexity import assess_complexity

PRIMARY=[
 ('B1','What happens in the small intestine after food leaves the stomach?'),
 ('B2','How do lungs exchange oxygen and carbon dioxide?'),
 ('B3','How does a plant cell differ from an animal cell?'),
 ('B4','How do antibodies recognize pathogens?'),
 ('M1','Why is the graph of y = x squared a parabola?'),
 ('M2','What does the slope of y = 2x + 1 mean?'),
 ('M3','Why is the derivative a tangent slope?'),
 ('M4','Solve 2x + 3 = 11 step by step'),
 ('M5','How does a number line show negative fractions?'),
 ('P1','Why does a heavier block accelerate less under the same net force?'),
 ('P2','What is the difference between speed and velocity?'),
 ('P3','How does a series electrical circuit work?'),
 ('P4',"How do a wave's amplitude and frequency differ?"),
 ('C1','What happens when acid and base neutralize each other?'),
 ('C2','How does dilution change concentration?'),
 ('C3','Why do noble gases rarely react?'),
 ('CS1','Dry run a Python for-loop that sums [2, 4, 6]'),
 ('CS2','How does Tower of Hanoi work with 3 disks?'),
 ('CS3','How does binary search locate an item?'),
 ('CS4','What is recursion, using a small example?'),
 ('G1','How does the water cycle move water?'),
 ('H1','Why did the Industrial Revolution spread?'),
 ('E1','Why does demand sometimes decrease when price rises?'),
 ('L1','How do present perfect and simple past differ?'),
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topics',type=Path,help='JSON list of topic strings or {id,topic} objects')
    parser.add_argument('--offline',action='store_true',help='Block external Python HTTP; does NOT prove physical Wi-Fi off')
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--limit',type=int,default=24)
    parser.add_argument('--output',type=Path,default=Path('outputs/phase4-evidence/matrix.json'))
    parser.add_argument('--model',choices=ALLOWED_MODELS,default='qwen3:4b')
    parser.add_argument('--languages',nargs='+',choices=['en','hi','kn'],default=['en'])
    parser.add_argument('--multilingual-cases',nargs='*',help='Case IDs to attempt in every requested language; others remain English-only')
    parser.add_argument('--showcase-cases',nargs='*',help='Case IDs to export when --export is enabled')
    parser.add_argument('--export',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--cpu',action='store_true',help='Actually request CPU-only local inference/voices in this process')
    args=parser.parse_args();os.environ['BLU_PLANNER_MODEL']=args.model
    source_files=sorted(Path('backend/app').glob('*.py'))+sorted(Path('frontend/src/visuals').glob('*.ts*'))
    source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    engine_hash=hashlib.sha256(json.dumps(source_hashes,sort_keys=True).encode()).hexdigest()
    if args.cpu:
        os.environ['CUDA_VISIBLE_DEVICES']='-1';os.environ['DEV']='cpu'
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE'):os.environ[key]='1'
    if args.offline:
        import urllib.request
        from urllib.parse import urlparse
        original=urllib.request.OpenerDirector.open
        def local_only(self,url,*a,**kw):
            actual=url.full_url if hasattr(url,'full_url') else url
            if urlparse(actual).hostname not in ('localhost','127.0.0.1'):raise OSError('Offline harness blocked external HTTP')
            return original(self,url,*a,**kw)
        urllib.request.OpenerDirector.open=local_only
    topics=PRIMARY
    if args.topics:
        raw=json.loads(args.topics.read_text(encoding='utf-8-sig'))
        topics=[(r.get('id',f'U{i+1}'),r['topic']) if isinstance(r,dict) else (f'U{i+1}',r) for i,r in enumerate(raw)]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    records=json.loads(args.output.read_text(encoding='utf-8')) if args.resume and args.output.exists() else []
    completed={r['case'] for r in records}
    for case,topic in topics[:args.limit]:
        if case in completed:continue
        start=time.perf_counter();row={'case':case,'topic':topic,'model':args.model,'seed':args.seed,
            'engine_sha256':engine_hash,
            'duration_mode':'auto','level':'beginner','human_scores':None,'reviewer':None,
            'physical_offline':'NOT VERIFIED','external_python_http_blocked':args.offline,'languages':{}}
        try:
            calls=[]
            def send(payload):
                payload={**payload,'options':{**payload['options'],'seed':args.seed}}
                if args.cpu:payload['options']['num_gpu']=0
                t=time.perf_counter();result=post_to_local_ollama(payload)
                calls.append({'seconds':round(time.perf_counter()-t,3),'kind':'lesson','eval_count':result.get('eval_count')})
                row.setdefault('raw_source_responses',[]).append(result.get('message',{}).get('content'))
                args.output.with_suffix('.progress.json').write_text(json.dumps({**row,'calls':calls},ensure_ascii=False,indent=2),encoding='utf-8')
                return result
            def review_send(payload):
                payload={**payload,'options':{**payload['options'],'seed':args.seed}}
                if args.cpu:payload['options']['num_gpu']=0
                t=time.perf_counter();result=post_to_local_ollama(payload)
                calls.append({'seconds':round(time.perf_counter()-t,3),'kind':'factual_review','eval_count':result.get('eval_count')})
                row.setdefault('raw_factual_reviews',[]).append(result.get('message',{}).get('content'))
                args.output.with_suffix('.progress.json').write_text(json.dumps({**row,'calls':calls},ensure_ascii=False,indent=2),encoding='utf-8')
                return result
            req=GenerateRequest(topic=topic,duration_mode='auto',target_seconds=60)
            source,lesson=plan_timed_lesson(req,transport=send,review_transport=review_send)
            evidence=json.loads(row['raw_source_responses'][-1]) if row.get('raw_source_responses') else None
            row.update(source=source,lesson=lesson.model_dump(),complexity=assess_complexity(lesson,req,evidence).model_dump())
            if source!='llm':raise ValueError('Source planner fallback: not a successfully taught lesson')
            from backend.app.visual_cache import save_teaching_intent
            save_teaching_intent(lesson,row['raw_source_responses'][-1])
            timeline=prepare_lesson(lesson,enforce_duration=True)
            def visual_send(payload):
                payload={**payload,'options':{**payload['options'],'seed':args.seed}}
                if args.cpu:payload['options']['num_gpu']=0
                t=time.perf_counter();result=post_to_local_ollama(payload)
                calls.append({'seconds':round(time.perf_counter()-t,3),'kind':'visual','eval_count':result.get('eval_count')})
                row.setdefault('raw_visual_responses',[]).append(result.get('message',{}).get('content'))
                return result
            visual=plan_visual(lesson,timeline['lesson_id'],model=args.model,transport=visual_send,force=True)
            plan=validate_plan(VisualPlan.model_validate(visual['plan']),lesson,timeline['lesson_id'])
            row.update(lesson_id=timeline['lesson_id'],visual_id=visual['visual_id'],visual_source=visual['visual_source'],
                fallback_reason=visual.get('fallback_reason'),families=[s.family for s in plan.scenes],
                scene_count=len(lesson.scenes),beat_count=sum(len(s['cues']) for s in timeline['scenes']),
                labels_missing=0,schema_valid=True,visual_plan=plan.model_dump(mode='json'),calls=calls)
            row['languages']['en']={'lesson_id':timeline['lesson_id'],'total_seconds':timeline['total_seconds']}
            for language in args.languages:
                if language=='en':continue
                if args.multilingual_cases is not None and case not in args.multilingual_cases:continue
                try:
                    from backend.app.localized_media import prepare_localized
                    from backend.app.visual_cache import attach_visual
                    loc=attach_visual(prepare_localized(timeline['lesson_id'],language,enforce_duration=True))
                    row['languages'][language]={'lesson_id':loc['lesson_id'],'total_seconds':loc['total_seconds'],
                        'visual_id':loc.get('visual_id'),'cue_counts':[len(s['cues']) for s in loc['scenes']]}
                except Exception as exc:row['languages'][language]={'error':str(exc)}
            if args.export and (args.showcase_cases is None or case in args.showcase_cases):
                from backend.app.live_export import export_lesson
                from backend.app.localized_export import export_localized
                for language,info in row['languages'].items():
                    if 'error' in info:continue
                    try:info['export']=(export_lesson if language=='en' else export_localized)(info['lesson_id'])
                    except Exception as exc:info['export_error']=str(exc)
        except Exception as exc:
            row['error']=str(exc);row['traceback']=traceback.format_exc()
        row['seconds']=round(time.perf_counter()-start,3);records.append(row)
        args.output.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:row.get(k) for k in ('case','source','visual_source','families','languages','seconds','error')},ensure_ascii=False),flush=True)
    print('MATRIX COMPLETE:',len(records),'actual cases; source llm:',sum(r.get('source')=='llm' for r in records),
          'visual llm:',sum(r.get('visual_source')=='llm' for r in records),'errors:',sum('error'in r for r in records),flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
