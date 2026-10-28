"""Couple safe visual data to an exact English lesson and narrated beats."""
from .visual_schema import VisualPlan, CodeData, AlgorithmData
from .algorithm_trace import safe_trace, hanoi, binary_search


def beat_texts(scene):
    if scene.type=='title_card':return [scene.narration]
    return [item.partition(' :: ')[2] or item for item in scene.items]


def ground_illustration_parts(raw,lesson):
    """Complete a MODEL-SELECTED installed template from parts actually spoken.

    This does not select a template or infer a biological relationship. It adds
    only catalog part names present in the source, and focuses them on that beat.
    All added strings go through the same localized display dictionary.
    """
    import copy,re
    from .visual_schema import ANCHORS,anchor_matches
    result=copy.deepcopy(raw)
    for spec,scene in zip(result.get('scenes',[]),lesson.scenes):
        template=spec.get('template_id')
        if spec.get('family')!='labelled_illustration' or template not in ANCHORS:continue
        texts=beat_texts(scene)
        actions=spec.get('beat_actions',[])
        entities=spec.get('entities',[])
        dictionary=spec.get('display_text_en',{})
        for entity in entities:
            label=dictionary.get(entity['label_key'],'').strip().lower().replace('_',' ')
            if entity.get('anchor_id') is None:
                exact=next((a for a in ANCHORS[template] if label==a.replace('_',' ')),None)
                if exact:entity.update(anchor_id=exact,role='part')
        for beat,text in enumerate(texts):
            mentions=[]
            for anchor in ANCHORS[template]:
                names={'villi':('villi','villus'),'bloodstream':('bloodstream','blood stream','blood vessel'),
                       'roots':('roots','root')}.get(anchor,(anchor.replace('_',' '),))
                offsets=[m.start() for name in names for m in re.finditer(r'\b'+re.escape(name)+r'\b',text,re.I)]
                if offsets:mentions.append((min(offsets),anchor))
            targets=[]
            for _,anchor in sorted(mentions):
                entity=next((e for e in entities if e.get('anchor_id')==anchor and anchor_matches(anchor,dictionary.get(e['label_key'],''))),None)
                if entity is None and len(entities)<12:
                    identifier='part_'+anchor
                    if any(e['id']==identifier for e in entities):continue
                    dictionary[identifier]=anchor.replace('_',' ').capitalize()
                    entity={'id':identifier,'role':'part','label_key':identifier,'anchor_id':anchor}
                    entities.append(entity)
                if entity:targets.append(entity['id'])
            if targets:
                spec['data']={**spec['data'],'zoom':'focused_part'}
                if not any(a['beat_index']==beat and a['op']=='zoom_region' for a in actions):
                    actions.append({'beat_index':beat,'op':'zoom_region','target_ids':[targets[0]]})
                if not any(a['beat_index']==beat and a['op']=='highlight' and a['target_ids']==targets[:4] for a in actions):
                    actions.append({'beat_index':beat,'op':'highlight','target_ids':targets[:4]})
        spec.update(entities=entities,display_text_en=dictionary,beat_actions=actions)
    return result


def validate_plan(plan: VisualPlan, lesson, source_id: str) -> VisualPlan:
    from .live import lesson_id
    if lesson_id(lesson)!=source_id:raise ValueError('Visual source ID is not the canonical English lesson hash')
    if plan.source_lesson_id != source_id:raise ValueError('Visual source_lesson_id mismatch')
    if len(plan.scenes)!=len(lesson.scenes):raise ValueError('Visual scene count mismatch')
    for spec,scene in zip(plan.scenes,lesson.scenes):
        import re
        evidence=(scene.heading+'; '+scene.narration).lower()
        if spec.family=='labelled_illustration':
            # One installed object cannot demonstrate the presence of a part
            # in one object and its absence in another. A labelled comparison
            # or explicit relationship map can express that distinction safely.
            from .visual_schema import ANCHORS
            for text in beat_texts(scene):
                absence=re.search(r'\b(?:lacks?|without|absent|does\s+not\s+(?:have|contain)|do\s+not\s+(?:have|contain)|no)\b',text,re.I)
                names=[a.replace('_',' ') for a in ANCHORS[spec.template_id]]
                if absence and any(re.search(r'\b'+re.escape(name)+r'\b',text,re.I) for name in names):
                    raise ValueError('A single installed illustration cannot assert part absence/presence across objects; use comparison or an explicit relationship diagram')
            # Installed templates include peripheral context anchors. Those
            # alone cannot establish that the depicted object is actually taught.
            core={
                'human_digestive_system':{'mouth','esophagus','stomach','pancreas','small_intestine','large_intestine','villi'},
                'human_heart':{'right_atrium','right_ventricle','left_atrium','left_ventricle'},
                'plant_cell':{'cell_wall','nucleus','chloroplast','vacuole','mitochondrion'},
                'animal_cell':{'nucleus','mitochondrion'},
                'leaf_photosynthesis':{'leaf','chloroplast'},
            }
            if not any(e.anchor_id in core[spec.template_id] for e in spec.entities):
                raise ValueError('Illustration is grounded only by peripheral context, not a supported structural part; use an explicit relationship diagram')
        if spec.family=='function_plot':
            from .algorithm_trace import math_function_from_text,bounded_math_value,function_value
            source_context=(lesson.title+'; '+lesson.scenes[0].heading+'; '+lesson.scenes[0].narration).lower()
            expression=math_function_from_text(evidence) or math_function_from_text(source_context)
            explicit=expression is not None
            schematic='schematic' in spec.display_text_en[spec.data.curve_label_key].lower()
            if not explicit and not (schematic and re.search(r'graph|curve|axes|axis',evidence)):
                raise ValueError('Numeric plot is not grounded in a spoken function; use actual relationships instead of inventing a curve')
            if expression:
                for index in range(17):
                    x=spec.data.x_min+(spec.data.x_max-spec.data.x_min)*index/16
                    expected=bounded_math_value(expression,x)
                    actual=function_value(spec.data.model_dump(),x)
                    if (expected is None)!=(actual is None) or (expected is not None and abs(expected-actual)>1e-6*max(1,abs(expected))):
                        raise ValueError(f'Plot parameters contradict the narrated equation {expression} at x={x:g}')
        count=len(beat_texts(scene))
        if any(a.beat_index>=count for a in spec.beat_actions):raise ValueError('Visual action references nonexistent spoken beat')
        if set(a.beat_index for a in spec.beat_actions)!=set(range(count)):raise ValueError('Every narrated beat needs a visual action')
        if isinstance(spec.data,CodeData):
            if spec.data.code!=scene.code:raise ValueError('Visual code must equal source scene code')
            if spec.data.trace_mode=='bounded':
                states=safe_trace(spec.data.code)
                if any(a.state_index is not None and a.state_index>=len(states) for a in spec.beat_actions):raise ValueError('Trace state outside trusted result')
                if not any(a.op=='set_state' for a in spec.beat_actions):raise ValueError('Bounded code trace needs spoken state actions; otherwise use explanation mode')
                actions=sorted((a for a in spec.beat_actions if a.op=='set_state'),key=lambda a:a.beat_index)
                if actions[-1].state_index!=len(states)-1:raise ValueError('Bounded code walkthrough must reach its actual final state')
        if isinstance(spec.data,AlgorithmData):
            context=(lesson.title+' '+scene.heading+' '+scene.narration).lower()
            named=('hanoi' in context if spec.data.algorithm=='hanoi' else bool(re.search(r'binary[- ]search',context)))
            if not named:raise ValueError('Trusted algorithm is not named in the source lesson; do not substitute unrelated states')
            if spec.data.algorithm=='hanoi':
                numbers={'two':2,'three':3,'four':4,'2':2,'3':3,'4':4}
                stated=re.findall(r'\b(two|three|four|[234])[- ]disks?\b',context)
                if stated and any(numbers[n]!=spec.data.disks for n in stated):raise ValueError('Hanoi disk count differs from the spoken example')
            states=(hanoi(spec.data.disks) if spec.data.algorithm=='hanoi'
                    else binary_search(list(spec.data.values),spec.data.target))
            if any(a.state_index is not None and a.state_index>=len(states) for a in spec.beat_actions):raise ValueError('Algorithm state outside trusted result')
            actions=sorted((a for a in spec.beat_actions if a.op=='set_state'),key=lambda a:a.beat_index)
            if not actions or actions[-1].state_index!=len(states)-1:raise ValueError('Algorithm must reach the complete trusted final state')
            if any(a.state_index>b.state_index for a,b in zip(actions,actions[1:])):raise ValueError('Algorithm actions must advance monotonically')
    return plan


def normalize_numeric_plan(raw,lesson):
    """Typed numeric reconstruction is computation from the spoken rule, not a guessed graph."""
    import copy
    from .visual_schema import PlotData
    from .algorithm_trace import math_function_from_text,verified_function_parameters,function_value
    data=copy.deepcopy(raw);notes=[]
    global_text=lesson.title+'; '+lesson.scenes[0].heading+'; '+lesson.scenes[0].narration
    for index,spec in enumerate(data.get('scenes',[])):
        if spec.get('family')!='function_plot':continue
        try:
            original=PlotData.model_validate(spec['data'])  # Invalid numeric JSON still fails closed.
            scene=lesson.scenes[index]
            expression=math_function_from_text(scene.heading+'; '+scene.narration) or math_function_from_text(global_text)
            if expression is None:continue
            parameters=verified_function_parameters(expression)
            if parameters is None:continue
            updated={**original.model_dump(mode='json'),**parameters}
            values=[function_value(updated,original.x_min+(original.x_max-original.x_min)*i/40) for i in range(41)]
            finite=[v for v in values if v is not None]
            if finite and max(map(abs,finite))<=9000:
                minimum,maximum=min(finite),max(finite);margin=max(.5,(maximum-minimum)*.1)
                updated.update(y_min=max(-10000,minimum-margin),y_max=min(10000,maximum+margin))
            legend=original.curve_label_key
            if legend in {e['label_key'] for e in spec['entities']}:legend='computed_curve'
            spec['display_text_en'][legend]='y = '+expression
            updated['curve_label_key']=legend
            spec['data']=PlotData.model_validate(updated).model_dump(mode='json')
            notes.append({'scene_index':index,'source_equation':expression,'method':'bounded independently checked typed function reconstruction'})
        except (ValueError,KeyError,IndexError,TypeError):continue
    return data,notes


def computed_data(spec,source_scene=None):
    """Trusted derived values are never supplied by a model or translation."""
    from .algorithm_trace import plot_samples, function_value
    d=spec.data
    if d.kind=='function_plot':
        data=d.model_dump()
        result={'samples':plot_samples(data),'points':[[x,function_value(data,x)] for x in d.point_xs]}
        if d.tangent_x is not None:
            x=d.tangent_x; h=1e-5; left,right=function_value(data,x-h),function_value(data,x+h)
            if left is not None and right is not None:result['tangent']={'x':x,'y':function_value(data,x),'slope':(right-left)/(2*h)}
        if d.secant_x is not None and d.tangent_x is not None:
            a,b=d.tangent_x,d.secant_x; ya,yb=function_value(data,a),function_value(data,b)
            if ya is not None and yb is not None and abs(a-b)>1e-8:result['secant']={'x':a,'y':ya,'slope':(yb-ya)/(b-a)}
            if ya is not None:
                samples=[]
                for i in range(61):
                    x=a+(b-a)*(1-i/60);y=function_value(data,x)
                    if abs(x-a)<1e-6:
                        samples.append(result.get('tangent',{'x':a,'y':ya,'slope':0}))
                    elif y is not None:samples.append({'x':a,'y':ya,'slope':(y-ya)/(x-a)})
                result['secant_path']=samples
        return result
    if d.kind=='algorithm_state':return {'states':hanoi(d.disks) if d.algorithm=='hanoi' else binary_search(list(d.values),d.target)}
    if d.kind=='code_trace':
        try:
            if d.trace_mode=='bounded':return {'states':safe_trace(d.code)}
            from .live import visual_beats
            lines=[b['highlight_lines'][0] if b['highlight_lines'] else 1 for b in visual_beats(source_scene)] if source_scene else []
            return {'states':[],'explanation_lines':lines}
        except ValueError:return {'states':[]}
    if d.kind in ('formula','equation_balance') and d.linear_equation:
        a,b,c=d.linear_equation
        return {'equation_steps':[f'{a:g}x + ({b:g}) = {c:g}',f'{a:g}x = {c-b:g}',f'x = {(c-b)/a:g}']}
    if d.kind=='force_motion' and d.mode=='force':
        net=[sum(getattr(v,axis) for v in d.vectors if v.unit=='N') for axis in ('x','y')]
        return {'net_force':net,'acceleration':[v/d.mass_kg for v in net]}
    return {}
