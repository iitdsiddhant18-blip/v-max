"""Cache safety regressions using isolated, synthetic PCM only."""
import json
import pytest
from backend.app.localized_media import prepare_localized, localized_folder, load_localized
from backend.tests.test_localized_media import FakeTranslator, make_pcm16_wav, prepared_english


def test_renderer_revision_migration_preserves_plan_and_previous_envelope(tmp_path):
    from backend.app.visual_cache import save_visual,load_visual,visual_id
    from backend.app.visual_planner import generic_visual
    from backend.app.live import lesson_id
    from backend.tests.test_visual_schema import teaching_lesson
    lesson=teaching_lesson();identifier=lesson_id(lesson);plan=generic_visual(lesson,identifier)
    envelope=save_visual(plan,lesson,root=tmp_path)
    envelope.update(renderer_revision='rich-svg-2.1',visual_id=visual_id(plan,'rich-svg-2.1'))
    file=tmp_path/identifier/'current.json';file.write_text(json.dumps(envelope),encoding='utf-8')
    revised=load_visual(identifier,lesson,root=tmp_path)
    assert revised['plan']==envelope['plan'] and revised['visual_id']!=envelope['visual_id']
    assert (file.parent/(envelope['visual_id']+'.plan.json')).is_file()


def test_render_identity_changes_when_speech_clock_or_voice_changes(tmp_path):
    from backend.app.visual_cache import save_visual,attach_visual
    from backend.app.visual_planner import generic_visual
    from backend.app.live import lesson_id
    from backend.tests.test_visual_schema import teaching_lesson
    lesson=teaching_lesson();identifier=lesson_id(lesson)
    save_visual(generic_visual(lesson,identifier),lesson,root=tmp_path)
    manifest={'lesson_id':identifier,'lesson':lesson.model_dump(),'language':'en','voice':'old','total_seconds':40,'scenes':[]}
    original=attach_visual(manifest,root=tmp_path)
    revised=attach_visual({**manifest,'voice':'af_heart','total_seconds':42},root=tmp_path)
    assert original['visual_id']==revised['visual_id']
    assert original['render_id']!=revised['render_id']


@pytest.mark.parametrize('malformed',['null','[]','{"visual_id":17}','not JSON'])
def test_new_valid_plan_can_archive_any_malformed_previous_envelope(tmp_path,malformed):
    from backend.app.visual_cache import save_visual,load_visual
    from backend.app.visual_planner import generic_visual
    from backend.app.live import lesson_id
    from backend.tests.test_visual_schema import teaching_lesson
    lesson=teaching_lesson();identifier=lesson_id(lesson);folder=tmp_path/identifier
    folder.mkdir();(folder/'current.json').write_text(malformed,encoding='utf-8')
    result=save_visual(generic_visual(lesson,identifier),lesson,root=tmp_path)
    assert load_visual(identifier,lesson,root=tmp_path)==result
    archives=list(folder.glob('invalid-*.plan.json'))
    assert len(archives)==1 and archives[0].read_text(encoding='utf-8')==malformed


def fixed_speech(seconds):
    def speak(text, path, language):
        make_pcm16_wav(path, seconds)
    return speak


@pytest.mark.parametrize('total', [29, 91, float('nan')])
def test_ready_cache_tampered_duration_rebuilt(prepared_english, total):
    source, english, target = prepared_english
    options=dict(translator=FakeTranslator(), synthesize=fixed_speech(3),
                 root=target, source_root=english, enforce_duration=True)
    good=prepare_localized(source,'hi',**options)
    file=localized_folder(good['lesson_id'],target)/'timeline.json'
    bad={**good,'total_seconds':total}
    file.write_text(json.dumps(bad,ensure_ascii=False),encoding='utf-8')
    repaired=prepare_localized(source,'hi',**options)
    assert repaired['total_seconds']==good['total_seconds']
    assert 30 <= repaired['total_seconds'] <= 90
    assert list(target.glob('*.invalid-*'))


@pytest.mark.parametrize('field', ['source_lesson_id','lesson'])
def test_ready_cache_hash_tamper_rebuilt(prepared_english, field):
    source,english,target=prepared_english
    options=dict(translator=FakeTranslator(),synthesize=fixed_speech(3),
                 root=target,source_root=english,enforce_duration=True)
    good=prepare_localized(source,'hi',**options)
    file=localized_folder(good['lesson_id'],target)/'timeline.json'
    bad=json.loads(file.read_text(encoding='utf-8'))
    if field=='lesson':bad[field]['title']='A different topic'
    else:bad[field]='a'*64
    file.write_text(json.dumps(bad,ensure_ascii=False),encoding='utf-8')
    assert prepare_localized(source,'hi',**options)==good


@pytest.mark.parametrize('total', [45,75])
def test_valid_cache_returns_without_resynthesis(prepared_english, total):
    source,english,target=prepared_english
    options=dict(translator=FakeTranslator(),root=target,source_root=english,enforce_duration=True)
    # Source fixture has ten spoken facts and five half-second pauses.
    good=prepare_localized(source,'hi',synthesize=fixed_speech((total-2.5)/10),**options)
    assert good['total_seconds']==total
    def no_speech(*_):raise AssertionError('valid cache resynthesized')
    assert prepare_localized(source,'hi',synthesize=no_speech,**options)==good
    assert load_localized(good['lesson_id'],root=target,enforce_duration=True)==good


def test_corrupt_visual_is_replaced_by_specific_validated_fallback(tmp_path):
    from backend.app.visual_cache import save_visual,attach_visual
    from backend.app.visual_planner import generic_visual
    from backend.app.live import lesson_id
    from backend.tests.test_visual_schema import teaching_lesson
    lesson=teaching_lesson();identifier=lesson_id(lesson)
    save_visual(generic_visual(lesson,identifier),lesson,root=tmp_path)
    file=tmp_path/identifier/'current.json';bad=json.loads(file.read_text(encoding='utf-8'))
    bad['visual_id']='a'*64;file.write_text(json.dumps(bad),encoding='utf-8')
    manifest={'lesson_id':identifier,'lesson':lesson.model_dump(),'language':'en'}
    ready=attach_visual(manifest,root=tmp_path)
    assert ready['visual_source']=='fallback' and ready['visual_plan']['source_lesson_id']==identifier
    assert list(file.parent.glob('corrupt-*.json'))
    assert attach_visual({'lesson_id':'b'*64,'lesson':lesson.model_dump(),'language':'en'},root=tmp_path)=={
        'lesson_id':'b'*64,'lesson':lesson.model_dump(),'language':'en'}
