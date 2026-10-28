import pytest
from backend.app.schema import GenerateRequest,Lesson
from backend.app.lesson_complexity import assess_complexity
from backend.tests.test_visual_schema import teaching_lesson


def test_legacy_omitted_mode_is_manual_and_serialization_compatible():
    request=GenerateRequest(topic='An unfamiliar concept',target_seconds=45)
    assert request.duration_mode=='manual' and 'duration_mode' not in request.model_dump()
    assert assess_complexity(teaching_lesson(),request).target_seconds==45


def test_same_level_three_unfamiliar_fact_sets_have_distinct_auto_budgets():
    targets=[]
    for density in (1,4,8):
        data=teaching_lesson().model_dump(); fact='Requires a prior state before the next step, with example x = 2 + 3.'
        data['scenes'][1]['items']=[fact if density==1 else fact+str(i) for i in range(density)]
        if density==1:data['scenes'][1]['items']=['A basic distinction']
        data['scenes'][1]['heading']='A distinction' if density==1 else 'Example and prediction'
        if density==4:data['scenes'][1]['items']=['Next explanation part']*4
        score=assess_complexity(Lesson.model_validate(data),GenerateRequest(topic='Unfamiliar relation',duration_mode='auto'))
        targets.append(score.target_seconds)
        assert 30<=score.target_seconds<=90 and len(score.evidence)==4
    assert len(set(targets))==3,targets


@pytest.mark.parametrize('seconds',[30,60,90])
def test_manual_override_preserved(seconds):
    request=GenerateRequest(topic='Concept',duration_mode='manual',target_seconds=seconds)
    assert assess_complexity(teaching_lesson(),request).target_seconds==seconds
