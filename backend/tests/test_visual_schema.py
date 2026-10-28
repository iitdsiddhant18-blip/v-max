import copy,json,random
import pytest
from pydantic import ValidationError
from backend.app.visual_schema import VisualPlan,VisualScene
from backend.app.visual_validate import validate_plan
from backend.app.visual_cache import visual_id
from backend.app.visual_planner import generic_visual
from backend.app.schema import Lesson
from backend.app.live import lesson_id


def test_installed_illustration_focus_includes_spoken_parts_not_only_actor_pairs():
    from backend.app.visual_validate import ground_illustration_parts
    lesson=teaching_lesson();raw=generic_visual(lesson,lesson_id(lesson)).model_dump(mode='json')
    source=lesson.model_dump()
    source['scenes'][1]['items'][0]='Inside :: The nucleus inside the cell holds the genetic information.'
    source['scenes'][1]['narration']=' '.join(v.partition(' :: ')[2] for v in source['scenes'][1]['items'])
    lesson=Lesson.model_validate(source)
    raw['source_lesson_id']=lesson_id(lesson)
    spec=raw['scenes'][1];spec.update(family='labelled_illustration',template_id='animal_cell',data={'kind':'labelled_illustration'})
    spec['entities'][0].update(anchor_id='membrane',role='part')
    spec['display_text_en'][spec['entities'][0]['label_key']]='Cell membrane'
    grounded=ground_illustration_parts(raw,lesson)
    plan=validate_plan(VisualPlan.model_validate(grounded),lesson,lesson_id(lesson))
    nucleus=next(e for e in plan.scenes[1].entities if e.anchor_id=='nucleus')
    assert any(a.beat_index==0 and a.op=='zoom_region' and nucleus.id in a.target_ids for a in plan.scenes[1].beat_actions)
    assert not any(e.anchor_id=='mitochondrion' for e in plan.scenes[1].entities)
    # Mentioning anatomy cannot select a template for a generic scene.
    generic=generic_visual(lesson,lesson_id(lesson)).model_dump(mode='json')
    assert ground_illustration_parts(generic,lesson)==generic


def test_single_object_illustration_rejects_presence_absence_comparison():
    from backend.app.visual_validate import ground_illustration_parts
    source=teaching_lesson().model_dump()
    source['scenes'][1]['items'][0]='Contrast :: One cell has a membrane, while the other lacks that membrane.'
    source['scenes'][1]['narration']=' '.join(v.partition(' :: ')[2] for v in source['scenes'][1]['items'])
    lesson=Lesson.model_validate(source);identifier=lesson_id(lesson)
    raw=generic_visual(lesson,identifier).model_dump(mode='json');spec=raw['scenes'][1]
    spec.update(family='labelled_illustration',template_id='animal_cell',data={'kind':'labelled_illustration'})
    spec['entities'][0].update(anchor_id='membrane',role='part')
    spec['display_text_en'][spec['entities'][0]['label_key']]='Membrane'
    raw=ground_illustration_parts(raw,lesson)
    with pytest.raises(ValueError,match='part absence/presence'):
        validate_plan(VisualPlan.model_validate(raw),lesson,identifier)
    validate_plan(generic_visual(lesson,identifier),lesson,identifier)


def test_context_anchor_alone_cannot_justify_an_unrelated_installed_object():
    lesson=teaching_lesson();identifier=lesson_id(lesson)
    raw=generic_visual(lesson,identifier).model_dump(mode='json');spec=raw['scenes'][1]
    spec.update(family='labelled_illustration',template_id='human_heart',data={'kind':'labelled_illustration'})
    spec['entities'][0].update(anchor_id='body',role='context')
    spec['display_text_en'][spec['entities'][0]['label_key']]='Body'
    with pytest.raises(ValueError,match='peripheral context'):
        validate_plan(VisualPlan.model_validate(raw),lesson,identifier)


def test_algorithm_states_cannot_replace_an_unrelated_explanation():
    lesson=teaching_lesson();identifier=lesson_id(lesson)
    raw=generic_visual(lesson,identifier).model_dump(mode='json')
    raw['scenes'][1]=scene_for('algorithm_state')
    with pytest.raises(ValueError,match='algorithm is not named'):
        validate_plan(VisualPlan.model_validate(raw),lesson,identifier)
    data=lesson.model_dump();data['scenes'][1]['heading']='Tower of Hanoi with 3 disks'
    lesson=Lesson.model_validate(data);raw['source_lesson_id']=lesson_id(lesson)
    validate_plan(VisualPlan.model_validate(raw),lesson,lesson_id(lesson))


def teaching_lesson():
    return Lesson.model_validate({'title':'A measured relationship','scenes':[
        {'type':'title_card','heading':'What changes?','narration':'Follow one relationship and test a concrete example.'},
        {'type':'diagram','heading':'Mechanism and example','narration':'First fact. Second fact. Third fact.',
         'items':['Input :: A measured input changes the state of this system.',
                  'Process :: The mechanism connects the input to the result.',
                  'Result :: A concrete example lets us check that relationship.']},
        {'type':'step_list','heading':'Check the result','narration':'Check the relationship with a second input.',
         'items':['Check :: Check the relationship with a second input.']} ]})


def family_specs():
    return {
      'concept_map':{'kind':'concept_map','layout':'tree'},
      'flow_process':{'kind':'flow_process','layout':'cycle'},
      'generic_diagram':{'kind':'generic_diagram','layout':'row'},
      'labelled_illustration':{'kind':'labelled_illustration','zoom':'focused_part'},
      'function_plot':{'kind':'function_plot','function':'polynomial','coefficients':[0,0,1],
          'x_min':-3,'x_max':3,'y_min':-1,'y_max':10,'x_label_key':'x_axis','y_label_key':'y_axis',
          'curve_label_key':'curve','point_xs':[-2,0,2],'tangent_x':1,'secant_x':2},
      'number_line':{'kind':'number_line','minimum':-3,'maximum':3,'points':[-1.5,0,.5],
          'intervals':[{'start':-1.5,'end':.5,'start_closed':False}],'axis_label_key':'x_axis'},
      'data_chart':{'kind':'data_chart','chart':'bar','category_keys':['a','b','c'],
          'series':[{'label_key':'curve','values':[2,4,6]}],'x_label_key':'x_axis','y_label_key':'y_axis'},
      'force_motion':{'kind':'force_motion','mode':'force','mass_kg':2,
          'vectors':[{'entity_id':'one','x':6,'y':0,'unit':'N'},{'entity_id':'two','x':-2,'y':0,'unit':'N'}],
          'schematic_label_key':'note'},
      'formula':{'kind':'formula','expression_key':'equation','step_keys':['a','b','c'],'linear_equation':[2,3,11]},
      'equation_balance':{'kind':'equation_balance','expression_key':'equation','step_keys':['a','b','c'],'linear_equation':[2,3,11]},
      'reaction_equation':{'kind':'reaction_equation',
          'reactants':[{'formula':'H2','coefficient':2,'label_key':'a'},{'formula':'O2','coefficient':1,'label_key':'b'}],
          'products':[{'formula':'H2O','coefficient':2,'label_key':'c'}]},
      'lab_process':{'kind':'lab_process','apparatus':[
          {'entity_id':'one','shape':'pipette','volume_ml':20,'capacity_ml':40,'solute_units':0},
          {'entity_id':'two','shape':'beaker','volume_ml':30,'capacity_ml':100,'solute_units':3}],
          'source_id':'one','target_id':'two','transfer_ml':20,'illustration_label_key':'note'},
      'code_trace':{'kind':'code_trace','code':'total = 0\nfor n in [2, 4, 6]:\n    total += n\nprint(total)',
          'trace_mode':'bounded','variables_label_key':'a','output_label_key':'b','status_label_key':'note'},
      'algorithm_state':{'kind':'algorithm_state','algorithm':'hanoi','disks':3,'state_label_key':'note','pointer_keys':['a','b','c']},
      'timeline':{'kind':'timeline','events':[{'entity_id':'one','time_label_key':'a','order':0},
          {'entity_id':'two','time_label_key':'b','order':1},{'entity_id':'three','time_label_key':'c','order':2}]},
      'comparison':{'kind':'comparison','column_keys':['a','b'],'rows':[['curve','equation'],['x_axis','y_axis']]},
      'table':{'kind':'table','column_keys':['a','b'],'rows':[['curve','equation'],['x_axis','y_axis']]},
    }


def scene_for(family):
    data=copy.deepcopy(family_specs()[family])
    result={'scene_index':1,'family':family,'entities':[
        {'id':'one','role':'input','label_key':'a'}, {'id':'two','role':'process','label_key':'b'},
        {'id':'three','role':'output','label_key':'c'}],
        'relationships':[{'source':'one','target':'two','kind':'flow','label_key':'relation'},
                         {'source':'two','target':'three','kind':'flow','label_key':'relation'}],
        'display_text_en':{'a':'Input','b':'Process','c':'Result','relation':'Changes into',
          'x_axis':'Input value','y_axis':'Output value','curve':'Squared relationship',
          'equation':'2x + 3 = 11','note':'Educational illustration'},
        'beat_actions':[{'beat_index':i,'op':'highlight','target_ids':[id]} for i,id in enumerate(('one','two','three'))],
        'data':data}
    if family=='labelled_illustration':
        result['template_id']='human_digestive_system'
        for e,anchor,label in zip(result['entities'],('stomach','small_intestine','bloodstream'),('Stomach','Small intestine','Bloodstream')):
            e['anchor_id']=anchor; result['display_text_en'][e['label_key']]=label
    if family=='algorithm_state':
        result['display_text_en'].update(a='A',b='B',c='C')
        result['beat_actions']=[{'beat_index':i,'op':'set_state','target_ids':['one'],'state_index':state} for i,state in enumerate((1,4,7))]
    if family=='function_plot':
        result['beat_actions']=[{'beat_index':i,'op':'plot_to_x','target_ids':['one'],'value':x} for i,x in enumerate((-2,0,2))]
    return result


@pytest.mark.parametrize('family',list(family_specs()))
def test_every_family_round_trips(family):
    spec=VisualScene.model_validate(scene_for(family))
    assert VisualScene.model_validate_json(spec.model_dump_json())==spec


@pytest.mark.parametrize('change',[
 lambda s:s.update(family='unknown'),
 lambda s:s.update(template_id='fake_organ'),
 lambda s:s['entities'].append(s['entities'][0]),
 lambda s:s['entities'][0].update(label_key='missing'),
 lambda s:s['relationships'][0].update(target='absent'),
 lambda s:s['relationships'][0].update(target='one'),
 lambda s:s['beat_actions'][0].update(op='javascript'),
 lambda s:s['beat_actions'][0].update(target_ids=['missing']),
 lambda s:s['beat_actions'][0].update(op='pour'),
 lambda s:s['display_text_en'].update(a='<script>alert(1)</script>'),
 lambda s:s['data'].update(path='M0 0L2 2'),
 lambda s:s['data'].update(layout='position:absolute'),
 lambda s:s['entities'].extend([{'id':f'extra_{i}','role':'part','label_key':'a'} for i in range(15)]),
])
def test_hostile_or_invalid_structures_fail_closed(change):
    spec=scene_for('generic_diagram'); change(spec)
    with pytest.raises((ValueError,ValidationError)):VisualScene.model_validate(spec)


def test_anchor_and_scene_source_beat_validation():
    spec=scene_for('labelled_illustration');spec['entities'][0]['anchor_id']='fake_lobe'
    with pytest.raises(ValueError,match='anchor'):VisualScene.model_validate(spec)
    lesson=teaching_lesson();identifier=lesson_id(lesson); plan=generic_visual(lesson,identifier)
    with pytest.raises(ValueError,match='source'):validate_plan(plan,lesson,'a'*64)
    data=plan.model_dump();data['scenes'][1]['beat_actions'][0]['beat_index']=7
    with pytest.raises(ValueError,match='nonexistent'):validate_plan(VisualPlan.model_validate(data),lesson,identifier)


@pytest.mark.parametrize('value',[float('nan'),float('inf'),1e100])
def test_nonfinite_and_absurd_numeric_data_rejected(value):
    spec=scene_for('function_plot');spec['data']['x_max']=value
    with pytest.raises(ValueError):VisualScene.model_validate(spec)


def test_hash_deterministic_under_random_dictionary_order():
    lesson=teaching_lesson();plan=generic_visual(lesson,lesson_id(lesson)); expected=visual_id(plan)
    for seed in range(20):
        data=plan.model_dump(mode='json'); items=list(data['scenes'][1]['display_text_en'].items())
        random.Random(seed).shuffle(items);data['scenes'][1]['display_text_en']=dict(items)
        assert visual_id(VisualPlan.model_validate(data))==expected


def test_mismatched_family_payload_is_rejected_even_when_both_are_known():
    spec=scene_for('concept_map');spec['family']='generic_diagram'
    with pytest.raises(ValueError,match='Family/payload mismatch'):VisualScene.model_validate(spec)


def test_general_draft_without_code_keeps_facts_as_diagram_not_fake_program():
    from backend.app.live import lesson_from_draft
    from backend.app.schema import GenerateRequest
    raw={'title':'A conceptual relationship','hook':{'heading':'What changes?',
         'narration':'A measured mechanism connects the input to a visible result that we can check.'},
         'explanations':[],
         'worked_example':{'heading':'A worked case','purpose':'worked_example','type':'code_walkthrough',
         'code':None,'beats':[{'label':'Input','fact':'This measured input changes the state of the system in a visible way.',
            'source_label':'Input','relation_label':'changes','target_label':'State'},
            {'label':'Result','fact':'The changed state produces a result that can be checked against the input.',
            'source_label':'State','relation_label':'produces','target_label':'Result'}]},
         'recap':{'heading':'Check the case','beats':[{'label':'Result','fact':'The result follows from the specific mechanism that we described above.',
            'source_label':'Mechanism','relation_label':'produces','target_label':'Result'}]}}
    lesson=lesson_from_draft(json.dumps(raw),GenerateRequest(topic='An unfamiliar mechanism'))
    assert lesson.scenes[1].type=='diagram' and lesson.scenes[1].code is None
    assert lesson.scenes[1].narration.startswith('This measured input changes the state')


def test_unrelated_numeric_graph_cannot_replace_a_spoken_mechanism():
    lesson=teaching_lesson();identifier=lesson_id(lesson);data=generic_visual(lesson,identifier).model_dump(mode='json')
    data['scenes'][1]=scene_for('function_plot')
    with pytest.raises(ValueError,match='not grounded'):validate_plan(VisualPlan.model_validate(data),lesson,identifier)
