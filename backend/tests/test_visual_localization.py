import copy
import pytest
from backend.app.visual_localize import localize_visual,validate_overlay
from backend.app.visual_planner import generic_visual
from backend.app.live import lesson_id
from backend.tests.test_visual_schema import teaching_lesson


def test_chemical_subscripts_are_symbols_but_plain_words_need_translation():
    from backend.app.visual_localize import protected_visual_text
    assert protected_visual_text('O₂') and protected_visual_text('CO₂') and protected_visual_text('C₆H₁₂O₆')
    assert not protected_visual_text('oxygen') and not protected_visual_text('English only')


def test_prose_axis_label_is_not_sent_as_protected_subtraction(tmp_path):
    from backend.app.visual_schema import VisualPlan
    lesson=teaching_lesson();data=generic_visual(lesson,lesson_id(lesson)).model_dump(mode='json')
    data['scenes'][1]['display_text_en']['label_0']='y-axis'
    plan=VisualPlan.model_validate(data);received=[]
    def translate(texts,language):
        received.extend(texts)
        return ['हिंदी '+text for text in texts]
    overlay=localize_visual(plan,'hi',translate_many=translate,root=tmp_path)
    assert 'y axis' in received and 'y-axis' not in received
    assert overlay[1]['label_0'].startswith('हिंदी')


@pytest.mark.parametrize('language,prefix',[('hi','हिंदी '),('kn','ಕನ್ನಡ ')])
def test_text_overlay_preserves_all_semantic_ids_and_numbers(tmp_path,language,prefix):
    lesson=teaching_lesson();plan=generic_visual(lesson,lesson_id(lesson));before=plan.model_dump_json()
    overlay=localize_visual(plan,language,translate_many=lambda xs,lang:[prefix+x for x in xs],root=tmp_path)
    assert plan.model_dump_json()==before
    assert all(set(m)==set(s.display_text_en) for m,s in zip(overlay,plan.scenes))
    assert localize_visual(plan,language,translate_many=lambda *_:(_ for _ in ()).throw(AssertionError()),root=tmp_path)==overlay


@pytest.mark.parametrize('corruption',['missing','echo','empty','html'])
def test_label_corruption_fails_closed(corruption):
    lesson=teaching_lesson();plan=generic_visual(lesson,lesson_id(lesson));overlay=[{'label_0':'हिंदी'}]+[
        {k:'हिंदी '+v for k,v in s.display_text_en.items()} for s in plan.scenes[1:]]
    if corruption=='missing':overlay[1].pop(next(iter(overlay[1])))
    elif corruption=='echo':overlay[1][next(iter(overlay[1]))]='English only'
    elif corruption=='empty':overlay[1][next(iter(overlay[1]))]=''
    else:overlay[1][next(iter(overlay[1]))]='<svg onload=alert(1)>'
    with pytest.raises(ValueError):validate_overlay(plan,'hi',overlay)


@pytest.mark.parametrize('language,durations,expected',[
 ('hi',[1.5,2,1.5],[(0,1.5),(1.5,3.5),(3.5,5)]),
 ('kn',[2,2.5,1.5],[(0,2),(2,4.5),(4.5,6)]),
])
def test_real_synthetic_pcm_has_distinct_localized_three_beat_boundaries(tmp_path,language,durations,expected):
    import wave
    from backend.app.live import prepare_lesson
    from backend.app.localized_media import prepare_localized
    from backend.tests.test_localized_media import make_pcm16_wav,FakeTranslator
    lesson=teaching_lesson();source_root=tmp_path/'source';target_root=tmp_path/'localized'
    def source_voice(text,path):make_pcm16_wav(path,1,8000)
    english=prepare_lesson(lesson,root=source_root,synthesize=source_voice)
    lengths=iter([1,*durations,1])
    def target_voice(text,path,language):make_pcm16_wav(path,next(lengths),8000)
    target=prepare_localized(english['lesson_id'],language,source_root=source_root,root=target_root,
        translator=FakeTranslator(),synthesize=target_voice,enforce_duration=False)
    cues=target['scenes'][1]['cues']
    assert [(c['start_seconds'],c['end_seconds']) for c in cues]==expected
    assert [c['item_index'] for c in cues]==[0,1,2]
    with wave.open(str(target_root/target['lesson_id']/'scene_01.wav')) as w:
        assert w.getnframes()/w.getframerate()==sum(durations)
    from backend.app.subtitles import manifest_to_srt
    assert (target_root/target['lesson_id']/'subtitles.srt').read_text(encoding='utf-8')==manifest_to_srt(target)
