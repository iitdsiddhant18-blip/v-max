import pytest
from backend.app.algorithm_trace import hanoi,binary_search,safe_trace,function_value,plot_samples
from backend.app.visual_schema import VisualScene
from backend.tests.test_visual_schema import scene_for


def test_three_disk_hanoi_has_seven_legal_moves_and_correct_final():
    states=hanoi(3);assert len(states)==8
    assert states[-1]['rods']=={'a':[],'b':[],'c':[3,2,1]}
    for state in states:
        assert sorted(d for rod in state['rods'].values() for d in rod)==[1,2,3]
        assert all(rod==sorted(rod,reverse=True) for rod in state['rods'].values())
    assert states==hanoi(3)


def test_binary_search_shrinks_and_finds_correct_index():
    states=binary_search([1,3,5,7,9,11],9)
    assert states[-1]['mid']==4 and states[-1]['found']
    assert all(b['high']-b['low']<a['high']-a['low'] for a,b in zip(states,states[1:]))
    assert not binary_search([1,3,5],8)[-1]['found']


def test_bounded_ast_trace_sum_is_twelve_and_records_pointer():
    states=safe_trace('total = 0\nfor n in [2,4,6]:\n    total += n\nprint(total)')
    assert states[-1]['output']==['12']
    assert [s['variables']['total'] for s in states if s['line']==3]==[2,6,12]


@pytest.mark.parametrize('code',[
 'import os','open("secret")','while True:\n    pass','print((1).__class__)',
 'x=[i for i in range(100)]','for i in range(1000000):\n    print(i)',
 'x = 99999 * 99999','x = 1 // 0','exec("pass")','x = lambda: 1',
 'for i in range(12):\n    for j in range(12):\n        print(j)',
 'print("a" * 100000)',
])
def test_unsupported_trace_never_executes(code):
    with pytest.raises(ValueError):safe_trace(code)


def test_plot_numbers_and_discontinuities():
    d=VisualScene.model_validate(scene_for('function_plot')).data.model_dump()
    assert [function_value(d,x) for x in (-2,0,2)]==[4,0,4]
    d.update(function='reciprocal',x_min=-1,x_max=1,shift=0)
    assert function_value(d,0) is None
    assert None in plot_samples(d)
    with pytest.raises(ValueError):plot_samples(d,100000)


def test_spoken_output_list_must_match_trusted_trace_without_topic_matching():
    from backend.app.algorithm_trace import check_spoken_outputs
    check_spoken_outputs('for value in range(3):\n    print(value)','The loop prints 0, 1, and 2.')
    with pytest.raises(ValueError,match='contradicts'):
        check_spoken_outputs('for value in range(3):\n    print(value)','This program prints 1, 2, and 3.')


def test_stated_equations_are_checked_without_executing_expression_strings():
    from backend.app.algorithm_trace import math_expression_from_text,bounded_math_value
    assert math_expression_from_text('The rule y equals two x plus one, then check it.')=='2*x+1'
    assert bounded_math_value('2*x+1',3)==7
    assert bounded_math_value('x**2',-2)==4
    with pytest.raises(ValueError):bounded_math_value('__import__("os")',1)
    with pytest.raises(ValueError):bounded_math_value('x**999999',1)


def test_numeric_parameters_are_reconstructed_from_the_actual_equation():
    from backend.app.algorithm_trace import verified_function_parameters,math_function_from_text
    assert verified_function_parameters('x**2')['coefficients']==[0,0,1]
    assert verified_function_parameters('2*x+1')['coefficients']==[1,2]
    assert math_function_from_text('For x=3, y=3²=9; the full curve is y=x².')=='x**2'


@pytest.mark.parametrize('family,change',[
 ('function_plot',lambda d:d.update(x_min=2,x_max=2)),
 ('data_chart',lambda d:d['series'][0].update(values=[-1,2,3])),
 ('reaction_equation',lambda d:d['products'][0].update(coefficient=1)),
 ('lab_process',lambda d:d.update(transfer_ml=100)),
 ('algorithm_state',lambda d:d.update(disks=40)),
])
def test_numeric_and_conservation_failures(family,change):
    spec=scene_for(family);change(spec['data'])
    with pytest.raises(ValueError):VisualScene.model_validate(spec)
