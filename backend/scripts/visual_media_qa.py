"""Sequential real delivery from recorded English generation. No prepared topic answers."""
import argparse,copy,json,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from backend.app.schema import Lesson
from backend.app.live import load_lesson,prepare_lesson
from backend.app.visual_schema import VisualPlan
from backend.app.visual_planner import generic_visual,hydrate_visual,context_recovery
from backend.app.visual_cache import save_teaching_intent,save_visual,attach_visual
from backend.app.visual_validate import validate_plan,normalize_numeric_plan,ground_illustration_parts
from backend.app.localized_media import prepare_localized
from backend.app.subtitles import manifest_to_srt


def revalidate_record(row):
    """Revalidate actual recorded model data against final invariants; no new inference."""
    lesson=Lesson.model_validate(row['lesson']);identifier=row['lesson_id']
    source=row.get('raw_source_responses',[])
    if source:save_teaching_intent(lesson,source[-1])
    baseline=generic_visual(lesson,identifier);data=baseline.model_dump(mode='json');sources=[];reasons=[]
    try:
        raw=hydrate_visual(json.loads(row['raw_visual_responses'][-1]),baseline)
        raw,numeric_notes=normalize_numeric_plan(raw,lesson)
        raw=ground_illustration_parts(raw,lesson)
    except (ValueError,KeyError,TypeError):raw={};numeric_notes=[]
    for i in range(len(lesson.scenes)):
        candidate=baseline.model_dump(mode='json');accepted=None;reason=None
        try:
            candidate['scenes'][i]=raw['scenes'][i]
            accepted=validate_plan(VisualPlan.model_validate(candidate),lesson,identifier)
            sources.append('llm')
        except (ValueError,KeyError,IndexError,TypeError) as exc:
            reason=str(exc);sources.append('fallback')
            try:
                candidate['scenes'][i]=context_recovery(raw['scenes'][i])
                accepted=validate_plan(VisualPlan.model_validate(candidate),lesson,identifier)
            except (ValueError,KeyError,IndexError,TypeError):pass
        if accepted is not None:data['scenes'][i]=accepted.model_dump(mode='json')['scenes'][i]
        reasons.append(reason)
    plan=validate_plan(VisualPlan.model_validate(data),lesson,identifier)
    return save_visual(plan,lesson,source='llm' if all(s=='llm' for s in sources) else 'fallback',
                       reason=json.dumps(reasons,ensure_ascii=False) if any(reasons) else None,scene_sources=sources,numeric_notes=numeric_notes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/phase4-evidence/media.json')
    parser.add_argument('--cases',nargs='+',default=['B1','B2','M1','M4','P1','C2','CS1','H1','U1','U2','U3','U4','U5','U6'])
    parser.add_argument('--export-cases',nargs='*',default=['B1','M1','CS1'])
    parser.add_argument('--revalidate-only',action='store_true')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    rows=json.loads(args.matrix.read_text(encoding='utf-8'))
    results=json.loads(args.output.read_text(encoding='utf-8')) if args.resume and args.output.exists() else []
    done={r['case'] for r in results}
    for row in rows:
        if row['case'] in done:continue
        selected=row['case'] in args.cases
        if not selected and not args.revalidate_only:continue
        start=time.perf_counter();result={'case':row['case'],'languages':{},'human_language_review':'PENDING'}
        try:
            if not row.get('lesson_id'):raise ValueError('Source generation failed; no honest same-semantic delivery is possible')
            visual=revalidate_record(row)
            result.update(visual_source=visual['visual_source'],scene_sources=visual.get('scene_sources'),
                          families=[s['family'] for s in visual['plan']['scenes']],visual_id=visual['visual_id'])
            if not args.revalidate_only:
                english=load_lesson(row['lesson_id'])
                for language in ('en','hi','kn'):
                    then=time.perf_counter();info={}
                    try:
                        manifest=english if language=='en' else prepare_localized(row['lesson_id'],language,enforce_duration=True)
                        assert 30<=manifest['total_seconds']<=90
                        manifest=attach_visual(manifest)
                        assert manifest['visual_id']==visual['visual_id']
                        assert manifest['visual_plan']==visual['plan']
                        folder=args.output.parent/'manifests';folder.mkdir(exist_ok=True)
                        file=folder/f"{row['case']}-{language}.json"
                        file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
                        srt=manifest_to_srt(manifest)
                        (folder/f"{row['case']}-{language}.srt").write_text(srt,encoding='utf-8')
                        info.update(lesson_id=manifest['lesson_id'],source_lesson_id=manifest.get('source_lesson_id',manifest['lesson_id']),
                            total_seconds=manifest['total_seconds'],render_id=manifest['render_id'],
                            cue_counts=[len(s['cues']) for s in manifest['scenes']],manifest_path=str(file),
                            subtitle_cues=srt.count('-->'),sample_rate=manifest['sample_rate'])
                        if row['case'] in args.export_cases:
                            from backend.app.live_export import export_lesson
                            from backend.app.localized_export import export_localized
                            info['export']=(export_lesson if language=='en' else export_localized)(manifest['lesson_id'])
                    except Exception as exc:
                        info['error']=str(exc);info['traceback']=traceback.format_exc()
                    info['seconds']=round(time.perf_counter()-then,3);result['languages'][language]=info
                    print('DELIVERY',row['case'],language,json.dumps(info,ensure_ascii=False),flush=True)
                    # Persist after every actual language, including failures.
                    args.output.write_text(json.dumps([*results,result],ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as exc:
            result['error']=str(exc);result['traceback']=traceback.format_exc()
        result['seconds']=round(time.perf_counter()-start,3);results.append(result)
        args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print('MEDIA CASE',row['case'],result.get('families'),result.get('error'),flush=True)
    print('REAL DELIVERY COMPLETE',len(results),'cases; no synthetic voice is substituted',flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
