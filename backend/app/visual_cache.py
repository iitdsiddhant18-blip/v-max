"""Versioned atomic semantic sidecars, independent of existing audio caches."""
import hashlib,json,logging,os,tempfile
from pathlib import Path
from .media import ROOT
from .visual_schema import VisualPlan
from .visual_validate import validate_plan,computed_data

VISUAL_ROOT=ROOT/'backend/cache/visuals'
RENDERER_REVISION='rich-svg-2.2'
logger=logging.getLogger(__name__)


def save_teaching_intent(lesson,raw,*,root=VISUAL_ROOT):
    from .live import teaching_draft_contract,lesson_id
    draft=teaching_draft_contract().model_validate_json(raw)
    scenes=[[]]+[[{'source':b.source_label,'relation':b.relation_label,'target':b.target_label}
                  for b in s.beats] for s in [*draft.explanations,draft.worked_example,draft.recap]]
    identifier=lesson_id(lesson);folder=root/identifier;folder.mkdir(parents=True,exist_ok=True)
    payload={'source_lesson_id':identifier,'lesson':lesson.model_dump(),'relationships':scenes}
    payload['digest']=hashlib.sha256(canonical(payload).encode()).hexdigest()
    fd,temp=tempfile.mkstemp(dir=folder,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(canonical(payload))
        os.replace(temp,folder/'teaching_intent.json')
    finally:
        if Path(temp).exists():Path(temp).unlink()


def load_teaching_intent(lesson,source_id,*,root=VISUAL_ROOT):
    try:
        payload=json.loads((root/source_id/'teaching_intent.json').read_text(encoding='utf-8'))
        digest=payload.pop('digest',None)
        if digest!=hashlib.sha256(canonical(payload).encode()).hexdigest():return None
        if payload['source_lesson_id']!=source_id or payload['lesson']!=lesson.model_dump():return None
        rows=payload['relationships']
        if len(rows)!=len(lesson.scenes):return None
        for scene,row in zip(lesson.scenes[1:],rows[1:]):
            if len(row)!=len(scene.items):return None
            for edge in row:
                if set(edge)!=set(('source','relation','target')):return None
                if any(not isinstance(v,str) or not v.strip() or len(v)>70 or '<' in v or '>' in v or '://' in v for v in edge.values()):return None
        return rows
    except (OSError,ValueError,KeyError,TypeError):return None


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def visual_id(plan: VisualPlan,revision=RENDERER_REVISION):
    return hashlib.sha256(canonical({'plan':plan.model_dump(mode='json'),
        'renderer_revision':revision}).encode('utf-8')).hexdigest()


def save_visual(plan,lesson,*,source='llm',reason=None,root=VISUAL_ROOT,scene_sources=None,numeric_notes=None):
    validate_plan(plan,lesson,plan.source_lesson_id)
    identifier=visual_id(plan); folder=root/plan.source_lesson_id
    folder.mkdir(parents=True,exist_ok=True)
    envelope={'visual_id':identifier,'renderer_revision':RENDERER_REVISION,'visual_source':source,
              'fallback_reason':reason,'plan':plan.model_dump(mode='json')}
    if scene_sources is not None:envelope['scene_sources']=scene_sources
    if numeric_notes:envelope['numeric_derivation']=numeric_notes
    fd,temp=tempfile.mkstemp(prefix='visual_',suffix='.tmp',dir=folder)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(canonical(envelope))
        current=folder/'current.json'
        if current.exists():
            previous_bytes=current.read_bytes()
            try:
                previous=json.loads(previous_bytes)
                previous_id=previous.get('visual_id','') if isinstance(previous,dict) else ''
            except (ValueError,TypeError):previous_id=''
            if not (isinstance(previous_id,str) and len(previous_id)==64 and all(c in '0123456789abcdef' for c in previous_id)):
                previous_id='invalid-'+hashlib.sha256(previous_bytes).hexdigest()
            archived=folder/(previous_id+'.plan.json')
            if not archived.exists():archived.write_bytes(previous_bytes)
        os.replace(temp,current)
    finally:
        if Path(temp).exists():Path(temp).unlink()
    return envelope


def load_visual(source_id,lesson,*,root=VISUAL_ROOT):
    import re
    if not re.fullmatch('[0-9a-f]{64}',source_id):raise ValueError('Invalid visual source ID')
    file=root/source_id/'current.json'
    if not file.exists():return None
    try:
        envelope=json.loads(file.read_text(encoding='utf-8'))
        plan=validate_plan(VisualPlan.model_validate(envelope['plan']),lesson,source_id)
        revision=envelope['renderer_revision']
        if revision not in ('rich-svg-2.1',RENDERER_REVISION) or envelope['visual_id']!=visual_id(plan,revision):raise ValueError('Visual hash/revision mismatch')
        if revision!=RENDERER_REVISION:
            return save_visual(plan,lesson,source=envelope['visual_source'],reason=envelope.get('fallback_reason'),root=root,
                               scene_sources=envelope.get('scene_sources'),numeric_notes=envelope.get('numeric_derivation'))
        return envelope
    except (ValueError,KeyError,TypeError,OSError) as exc:
        logger.warning('Visual sidecar rejected %s: %s',source_id[:12],exc)
        return None


def attach_visual(manifest,*,root=VISUAL_ROOT,translate_many=None):
    from .schema import Lesson
    from .visual_localize import localize_visual
    source_id=manifest.get('source_lesson_id') or manifest['lesson_id']
    english=Lesson.model_validate(manifest.get('semantic_lesson') or manifest['lesson'])
    envelope=load_visual(source_id,english,root=root)
    if envelope is None:
        file=root/source_id/'current.json'
        if not file.exists():return manifest  # Genuine legacy manifest.
        from .visual_planner import generic_visual
        import uuid
        file.rename(file.with_name('corrupt-'+uuid.uuid4().hex+'.json'))
        envelope=save_visual(generic_visual(english,source_id),english,source='fallback',
                             reason='Stored visual sidecar failed source/hash/schema validation',root=root)
    plan=VisualPlan.model_validate(envelope['plan'])
    overlay=localize_visual(plan,manifest['language'],translate_many=translate_many,root=root)
    # A renderer revision alone cannot distinguish regenerated speech with the
    # same legacy semantic ID. Include actual PCM and its measured cue clock.
    audio={'voice':manifest.get('voice'),'revision':manifest.get('audio_revision'),
           'sample_rate':manifest.get('sample_rate'),'total_seconds':manifest.get('total_seconds'),
           'scenes':manifest.get('scenes',[])}
    import re
    identifier=manifest.get('lesson_id','')
    if re.fullmatch('[0-9a-f]{64}',identifier):
        namespace='lessons' if manifest['language']=='en' else 'localized'
        pcm=ROOT/'backend/cache'/namespace/identifier/'combined.wav'
        if pcm.is_file():
            with pcm.open('rb') as stream:audio['pcm_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    render_id=hashlib.sha256(canonical({'visual_id':envelope['visual_id'],'language':manifest['language'],
                                      'labels':overlay,'audio':audio}).encode()).hexdigest()
    return {**manifest,'visual_plan':envelope['plan'],'visual_id':envelope['visual_id'],'render_id':render_id,
            'visual_source':envelope['visual_source'],'visual_labels':overlay,
            'visual_computed':[computed_data(s,english.scenes[i]) for i,s in enumerate(plan.scenes)]}
