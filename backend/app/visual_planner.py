"""Local-only semantic planning; no topic-keyword dispatch or generated geometry."""
import copy,json,logging
from .visual_schema import VisualPlan,ANCHORS
from .visual_validate import validate_plan,beat_texts,normalize_numeric_plan,ground_illustration_parts
from .visual_cache import load_visual,save_visual,VISUAL_ROOT
from .planner import post_to_local_ollama,ALLOWED_MODELS

logger=logging.getLogger(__name__)
POLICY='''Design a semantic visual plan for the EXACT supplied narrated lesson.
Return only JSON matching the schema. Never invent new facts, coordinates, paths, HTML,
URLs or executable code. Every scene, including title/recap, needs a visual scene.
Choose visual family from the facts/relationships, never from a subject keyword rule.
Prefer a meaningful specialized behavior when its semantic data is available:
named supported object parts -> labelled_illustration; a numeric x/y relation ->
function_plot; solving an equality -> equation_balance; locations on a signed
axis -> number_line; force vectors -> force_motion; state transitions of a known
algorithm -> algorithm_state; dated/ordered events -> timeline; explicit contrasts
-> comparison. Do not choose generic_diagram for every scene just to avoid payloads.
Use short plain English labels in display_text_en; all *_key fields reference these keys.
IDs are ASCII semantic keys. Relationships use existing source/target IDs and a label_key.
Every spoken beat index requires at least one action targeting existing entity IDs.
Each action means that exact spoken fact: no unrelated motion. Use reveal/highlight for
context, trace_path for an actual relationship, set_state only with a valid trusted state.
Function plots use numeric typed function parameters only. polynomial coefficients are
ascending [constant,x,x²,...]. Mark points using point_xs; trusted code computes y.
Code trace MUST copy actual scene code exactly; bounded only for simple assignments,
literal-list for, range, arithmetic, if and print. Otherwise explanation mode.
Algorithm_state chooses hanoi (2–4 disks; trusted local solver) or binary_search (sorted values).
Hanoi 3 disks has states 0–7. Map narrated move groups to appropriate increasing states.
No fake anatomical assets. Templates/allowed anchors:
human_digestive_system: mouth,esophagus,stomach,pancreas,small_intestine,large_intestine,villi,bloodstream
human_heart: right_atrium,right_ventricle,left_atrium,left_ventricle,lungs,body
plant_cell: cell_wall,membrane,nucleus,cytoplasm,chloroplast,vacuole,mitochondrion
animal_cell: membrane,nucleus,cytoplasm,mitochondrion
leaf_photosynthesis: leaf,chloroplast,roots,stem,air,sugar,oxygen
Only labelled_illustration has template_id and anchor_id; others use null.
Each illustration entity label MUST explicitly name its actual supported anchor.
Do not relabel a broad anchor as an unsupported precise part; use a concept map instead.
Unknown anatomy uses concept_map with explicit compartments and directed exchange edges.
force_motion modes force/motion/circuit/wave choose the physical relation actually taught.
Reaction formulas must conserve atoms; lab_process volumes must conserve volume and capacity.
No invented numerical measurements or dates. Formula can use a typed linear_equation [a,b,c]
for ax+b=c; trusted code derives steps. A comparison/table localizes every cell via text keys.
generic_diagram is an honest relevant relationship fallback, not an unrelated picture.
Use 2–6 entities when possible. Title/recap may use simple maps. Keep labels concise.
Presence/absence contrasts across different objects require comparison or an
explicit relationship map. A single installed object illustration cannot show
both having and lacking the same part. Do not reuse it for every comparison beat.
'''


def generic_visual(lesson,source_id,*,root=VISUAL_ROOT):
    """Preserve actual lesson facts and ordering; do not invent mechanisms or anatomy."""
    from .visual_cache import load_teaching_intent
    intent=load_teaching_intent(lesson,source_id,root=root)
    scenes=[]
    for i,s in enumerate(lesson.scenes):
        if intent and intent[i]:
            concepts=[];text={};edges=[];actions=[]
            for beat,edge in enumerate(intent[i]):
                pair=[]
                for label in (edge['source'],edge['target']):
                    label=' '.join(label.replace('_',' ').split())
                    existing=next((j for j,value in enumerate(concepts)
                                   if (value==label if s.code or len(label)==1 else value.casefold()==label.casefold())),None)
                    if existing is None:concepts.append(label);existing=len(concepts)-1
                    pair.append(existing)
                source,target=pair
                if source!=target:
                    text[f'relation_{beat}']=edge['relation']
                    edges.append({'source':f'idea_{source}','target':f'idea_{target}',
                                  'kind':'flow','label_key':f'relation_{beat}'})
                actions.append({'beat_index':beat,'op':'trace_path' if source!=target else 'highlight',
                                'target_ids':list(dict.fromkeys(f'idea_{n}' for n in pair))})
            text.update({f'label_{j}':v for j,v in enumerate(concepts)})
            scenes.append({'scene_index':i,'family':'generic_diagram',
                'entities':[{'id':f'idea_{j}','role':'process','label_key':f'label_{j}'} for j in range(len(concepts))],
                'relationships':edges,'display_text_en':text,'beat_actions':actions,
                'data':{'kind':'generic_diagram','layout':'row'}})
            continue
        labels=[s.heading] if s.type=='title_card' else [v.partition(' :: ')[0] for v in s.items]
        labels=labels[:8] or [s.heading]
        labels=[v.replace('<','‹').replace('>','›')[:120] for v in labels]
        text={f'label_{j}':v for j,v in enumerate(labels)}
        entities=[{'id':f'idea_{j}','role':'process','label_key':f'label_{j}'} for j in range(len(labels))]
        edges=[]
        for j in range(len(labels)-1):
            key=f'relation_{j}'
            # This asserts explanation sequence, not an invented causal claim.
            text[key]='Following idea'
            edges.append({'source':f'idea_{j}','target':f'idea_{j+1}','kind':'sequence','label_key':key})
        actions=[{'beat_index':j,'op':'highlight','target_ids':[f'idea_{min(j,len(labels)-1)}']} for j in range(len(beat_texts(s)))]
        scenes.append({'scene_index':i,'family':'generic_diagram','entities':entities,'relationships':edges,
                       'display_text_en':text,'beat_actions':actions,'data':{'kind':'generic_diagram','layout':'row'}})
    for spec,source_scene in zip(scenes,lesson.scenes):
        if source_scene.type=='code_walkthrough' and source_scene.code:
            spec['family']='code_trace'
            spec['display_text_en'].update(fallback_variables='Variables',fallback_output='Output',
                fallback_status='Explanation only: no execution trace')
            spec['data']={'kind':'code_trace','code':source_scene.code,'trace_mode':'explanation',
                'variables_label_key':'fallback_variables','output_label_key':'fallback_output',
                'status_label_key':'fallback_status'}
            for action in spec['beat_actions']:action['op']='highlight'
    return validate_plan(VisualPlan.model_validate({'source_lesson_id':source_id,'scenes':scenes}),lesson,source_id)


def _specialized_schema(schema, families, baseline=None, lesson=None):
    result=copy.deepcopy(schema); definitions=result['$defs']; base=definitions['VisualScene']
    variants={}
    for option in base['properties']['data']['oneOf']:
        name=option['$ref'].split('/')[-1]; kind=definitions[name]['properties']['kind']
        for family in kind.get('enum',[kind.get('const')]):variants[family]=name
    prefixes=[]
    for i,family in enumerate(families):
        item=copy.deepcopy(base);item['properties']['scene_index']={'type':'integer','const':i}
        item['properties']['family']={'type':'string','const':family}
        item['properties']['data']={'$ref':'#/$defs/'+variants[family]}
        if baseline is not None:
            source=baseline.scenes[i]
            # The source pass already described the objects and directed facts.
            # Own their IDs, labels, edges and beat cardinality here instead of
            # asking a small model to reconstruct fragile reference plumbing.
            entity_variants=[]
            for entity in source.entities:
                e=entity.model_dump(mode='json');fields={k:{'const':v} for k,v in e.items() if k!='anchor_id'}
                fields['anchor_id']=({'anyOf':[{'type':'null'},{'type':'string','enum':sorted({a for values in ANCHORS.values() for a in values})}]}
                                      if family=='labelled_illustration' else {'type':'null'})
                entity_variants.append({'type':'object','properties':fields,'required':list(fields),'additionalProperties':False})
            item['properties']['entities']={'type':'array','prefixItems':entity_variants,'minItems':len(entity_variants),'maxItems':len(entity_variants)}
            item['properties']['relationships']={'const':[r.model_dump(mode='json') for r in source.relationships]}
            extras={
                'function_plot':['x_axis','y_axis','curve'],'number_line':['x_axis'],
                'data_chart':['x_axis','y_axis'],'force_motion':['note'],
                'formula':['equation','step_0','step_1','step_2'],
                'equation_balance':['equation','step_0','step_1','step_2'],
                'lab_process':['note'],'code_trace':['variables','output','note'],
                'algorithm_state':['state','rod_a','rod_b','rod_c'],
                'timeline':[f'time_{j}' for j in range(len(source.entities))],
                'comparison':['column_a','column_b'],'table':['column_a','column_b'],
            }.get(family,[])
            props={k:{'type':'string','const':v} for k,v in source.display_text_en.items()}
            props.update({k:{'type':'string','minLength':1,'maxLength':100} for k in extras})
            item['properties']['display_text_en']={'type':'object','properties':props,'required':list(props),'additionalProperties':False}
            def narrow(node,key=''):
                if '$ref' in node:return narrow(copy.deepcopy(definitions[node['$ref'].split('/')[-1]]),key)
                if key.endswith('_key') or key in ('category_keys','column_keys','rows','step_keys','pointer_keys'):
                    if node.get('type')=='string':return {'type':'string','enum':list(props)}
                if key in ('entity_id','source_id','target_id') and node.get('type')=='string':
                    return {'type':'string','enum':[e.id for e in source.entities]}
                if 'properties' in node:
                    node['properties']={k:narrow(v,k) for k,v in node['properties'].items()}
                if 'items' in node:node['items']=narrow(node['items'],key)
                if 'prefixItems' in node:node['prefixItems']=[narrow(v,key) for v in node['prefixItems']]
                for union in ('anyOf','oneOf'):
                    if union in node:node[union]=[narrow(v,key) for v in node[union]]
                return node
            payload=narrow(copy.deepcopy(definitions[variants[family]]))
            payload['properties']['kind']={'type':'string','const':family}
            if family=='code_trace' and lesson.scenes[i].code:
                payload['properties']['code']={'type':'string','const':lesson.scenes[i].code}
            item['properties']['data']=payload
            count=len(beat_texts(lesson.scenes[i]))
            action_variants=[]
            for beat in range(count):
                action=copy.deepcopy(definitions['BeatAction'])
                action['properties']['beat_index']={'type':'integer','const':beat}
                action['properties']['target_ids']={'type':'array','items':{'type':'string','enum':[e.id for e in source.entities]},'minItems':1,'maxItems':2}
                if family in ('concept_map','flow_process','generic_diagram','labelled_illustration','comparison','table','timeline','data_chart'):
                    action['properties']['op']={'type':'string','enum':['reveal','highlight']}
                action_variants.append(action)
            item['properties']['beat_actions']={'type':'array','prefixItems':action_variants,'minItems':count,'maxItems':count}
            if family in ('concept_map','flow_process','generic_diagram','labelled_illustration'):
                item['properties']['beat_actions']={'const':[a.model_dump(mode='json') for a in source.beat_actions]}
        if family=='labelled_illustration':
            item['properties']['template_id']={'type':'string','enum':list(ANCHORS)}
            item.setdefault('required',[])
            if 'template_id' not in item['required']:item['required'].append('template_id')
            if baseline is None:
                entity=copy.deepcopy(definitions['Entity'])
                entity['properties']['anchor_id']={'type':'string','enum':sorted({a for values in ANCHORS.values() for a in values})}
                entity.setdefault('required',[])
                if 'anchor_id' not in entity['required']:entity['required'].append('anchor_id')
                item['properties']['entities']['items']=entity
        else:
            item['properties']['template_id']={'type':'null'}
        if baseline is not None:
            full=item['properties'];fixed=baseline.scenes[i]
            compact={'scene_index':full['scene_index'],'family':full['family'],
                     'template_id':full['template_id'],'data':full['data']}
            extra={k:v for k,v in full['display_text_en']['properties'].items() if k not in fixed.display_text_en}
            compact['texts']={'type':'object','properties':extra,'required':list(extra),'additionalProperties':False}
            if family=='labelled_illustration':
                anchor_type={'anyOf':[{'type':'null'},{'type':'string','enum':sorted({a for values in ANCHORS.values() for a in values})}]}
                compact['anchors']={'type':'object','properties':{e.id:anchor_type for e in fixed.entities},
                                    'required':[e.id for e in fixed.entities],'additionalProperties':False}
            if family not in ('concept_map','flow_process','generic_diagram','labelled_illustration'):
                compact['beat_actions']=full['beat_actions']
            item={'type':'object','properties':compact,'required':list(compact),'additionalProperties':False}
        prefixes.append(item)
    result['properties']['scenes']={'type':'array','prefixItems':prefixes,'minItems':len(prefixes),'maxItems':len(prefixes)}
    return result


def hydrate_visual(raw,baseline):
    """Expand compact model intent with trusted source IDs/edges/beats."""
    if all('entities' in s for s in raw.get('scenes',[])):return raw
    result={'visual_schema_version':2,'source_lesson_id':baseline.source_lesson_id,'scenes':[]}
    if len(raw.get('scenes',[]))!=len(baseline.scenes):raise ValueError('Compact visual scene count mismatch')
    for index,(draft,source) in enumerate(zip(raw['scenes'],baseline.scenes)):
        if draft['scene_index']!=index:raise ValueError('Compact scene order mismatch')
        spec=source.model_dump(mode='json');spec.update(family=draft['family'],template_id=draft.get('template_id'),data=draft['data'])
        extras=draft.get('texts',{})
        if set(extras)&set(spec['display_text_en']):raise ValueError('Compact intent cannot override source labels')
        spec['display_text_en'].update(extras)
        anchors=draft.get('anchors',{})
        if not set(anchors)<={e.id for e in source.entities}:raise ValueError('Compact anchor references missing entity')
        for e in spec['entities']:e['anchor_id']=anchors.get(e['id'])
        if 'beat_actions' in draft:spec['beat_actions']=draft['beat_actions']
        result['scenes'].append(spec)
    return result


def context_recovery(scene):
    """Remove false precision, never manufacture a new anatomical anchor."""
    from .visual_schema import anchor_matches
    result=copy.deepcopy(scene)
    if result.get('family')!='labelled_illustration' or result.get('template_id') not in ANCHORS:return result
    for entity in result.get('entities',[]):
        anchor=entity.get('anchor_id')
        if anchor is not None and (anchor not in ANCHORS[result['template_id']]
                or not anchor_matches(anchor,result['display_text_en'].get(entity.get('label_key'),''))):
            entity['anchor_id']=None
            entity['role']='context'
    return result


def plan_visual(lesson,source_id,*,model='qwen3:4b',transport=None,root=VISUAL_ROOT,force=False):
    if model not in ALLOWED_MODELS:raise ValueError('Unsupported installed model')
    cached=load_visual(source_id,lesson,root=root)
    if cached is not None and not force:return cached
    send=transport or post_to_local_ollama; feedback=''; previous=None
    baseline=generic_visual(lesson,source_id,root=root)
    facts=[{'scene_index':i,'heading':s.heading,'code':s.code,
            'beats':beat_texts(s),'labels':[v.partition(' :: ')[0] for v in s.items]}
           for i,s in enumerate(lesson.scenes)]
    schema=VisualPlan.model_json_schema()
    # Defaults are useful in stored contracts, but the model must emit the
    # discriminator explicitly. Otherwise Ollama can select an unrelated union.
    for definition in schema.get('$defs',{}).values():
        properties=definition.get('properties',{})
        if 'kind' in properties:
            definition.setdefault('required',[])
            if 'kind' not in definition['required']:definition['required'].append('kind')
    # A single existing entity is sufficient for the model's narrated focus.
    # Connectors are already explicit relationships; trusted drawing code traces
    # them when their target is focused. Avoid redundant second edge declarations.
    actions=schema['$defs']['BeatAction']['properties']
    actions['op']['enum']=['reveal','highlight','set_state','plot_to_x','secant_to_tangent','pour','emphasize_term','zoom_region']
    actions['target_ids']['maxItems']=1
    schema['properties']['source_lesson_id']={'type':'string','const':source_id}
    # Pick behaviors first, then constrain each positional payload to that family.
    # This keeps small local models from mixing fields from unrelated variants.
    from .visual_schema import Family
    from typing import get_args
    choices_schema=[]
    from .algorithm_trace import math_function_from_text
    global_context=lesson.title+'; '+lesson.scenes[0].heading+'; '+lesson.scenes[0].narration
    for index,source in enumerate(lesson.scenes):
        allowed=list(get_args(Family))
        text=source.heading+'; '+source.narration
        # Constrain by data prerequisites, never by a subject/topic route.
        if not (math_function_from_text(text) or math_function_from_text(global_context)):
            import re
            if not re.search(r'\b(graph|curve|axes|axis)\b',text,re.I):allowed.remove('function_plot')
        if not source.code:allowed.remove('code_trace')
        if not any(name in (lesson.title+' '+text).lower() for name in ('hanoi','binary search','binary-search')):
            allowed.remove('algorithm_state')
        has_installed_anchor = any(
            any(anchor.replace('_', ' ') in (text + ' ' + lesson.title).lower() for anchor in anchors)
            for anchors in ANCHORS.values()
        )
        if not has_installed_anchor and 'labelled_illustration' in allowed:
            allowed.remove('labelled_illustration')
        choices_schema.append({'type':'object','properties':{'scene_index':{'type':'integer','const':index},
            'heading':{'type':'string','const':source.heading},'evidence':{'type':'string','maxLength':160},
            'family':{'type':'string','enum':allowed}},
            'required':['scene_index','heading','evidence','family'],'additionalProperties':False})
    intent_schema={'type':'object','properties':{'choices':{'type':'array','prefixItems':choices_schema,
        'minItems':len(facts),'maxItems':len(facts)}},'required':['choices'],'additionalProperties':False}
    try:
        selection=send({'model':model,'messages':[{'role':'system','content':POLICY},
            {'role':'user','content':json.dumps({'task':'For each scene, first identify concrete evidence in its facts (parts, numeric relation, state transition, chronology, contrast). Then choose the best family that can actually draw that evidence. Generic diagrams are only for facts without a supported richer behavior. Return choices in source order.',
                                               'scenes':facts})}],
            'format':intent_schema,'think':False,'stream':False,'keep_alive':0,
            'options':{'temperature':0.1,'num_ctx':4096,'num_predict':1000}})
        choices=json.loads(selection['message']['content'])['choices']
        families=[c['family'] for c in choices]
        if len(families)!=len(facts) or any(f not in get_args(Family) for f in families):raise ValueError('Invalid visual family selection')
        if any(c.get('scene_index')!=i or c.get('heading')!=lesson.scenes[i].heading
               or c['family'] not in choices_schema[i]['properties']['family']['enum'] for i,c in enumerate(choices)):
            raise ValueError('Visual family selection did not preserve scene identity/data prerequisites')
        schema=_specialized_schema(schema,families,baseline,lesson)
    except (ValueError,KeyError,TypeError,OSError,TimeoutError) as exc:
        logger.warning('Visual family selection unavailable: %s',exc)
    for attempt in range(2):
        trusted=[]
        for index,family in enumerate(locals().get('families',[])):
            source_scene=lesson.scenes[index]
            if family=='code_trace' and source_scene.code:
                from .algorithm_trace import safe_trace
                try:trusted.append({'scene_index':index,'states':safe_trace(source_scene.code)})
                except ValueError as exc:trusted.append({'scene_index':index,'trace_available':False,'reason':str(exc),'required_mode':'explanation'})
            if family=='function_plot':
                from .algorithm_trace import math_expression_from_text,bounded_math_value
                text=source_scene.heading+' '+source_scene.narration
                expression=math_expression_from_text(text) or math_expression_from_text(lesson.title+' '+lesson.scenes[0].narration)
                if expression:
                    try:trusted.append({'scene_index':index,'stated_equation':expression,
                        'checked_points':[[x,bounded_math_value(expression,x)] for x in (-2,-1,0,1,2)]})
                    except ValueError:pass
        messages=[{'role':'system','content':POLICY}, {'role':'user','content':json.dumps({
            'source_lesson_id':source_id,'lesson_title':lesson.title,'scenes':facts,
            'selected_families':locals().get('families'),
            'semantic_reference':[{'scene_index':s.scene_index,
                'entities':[{'id':e.id,'label':s.display_text_en[e.label_key]} for e in s.entities],
                'edges':[{'source':r.source,'target':r.target,'label':s.display_text_en[r.label_key]} for r in s.relationships]}
                for s in baseline.scenes],
            'trusted_computations':trusted,
            'validation_feedback':feedback},ensure_ascii=False)}]
        if previous:messages.extend([{'role':'assistant','content':previous[:12000]},
            {'role':'user','content':'Repair the complete plan: '+feedback}])
        payload={'model':model,'messages':messages,'format':schema,'think':False,'stream':False,
                 'keep_alive':0,'options':{'temperature':0.1,'num_ctx':4096,'num_predict':4096}}
        try:
            response=send(payload); previous=response['message']['content']
            expanded=hydrate_visual(json.loads(previous),baseline)
            expanded,numeric_notes=normalize_numeric_plan(expanded,lesson)
            expanded=ground_illustration_parts(expanded,lesson)
            plan=validate_plan(VisualPlan.model_validate(expanded),lesson,source_id)
            return save_visual(plan,lesson,source='llm',root=root,numeric_notes=numeric_notes)
        except (ValueError,KeyError,TypeError,OSError,TimeoutError) as exc:
            feedback=str(exc)[:1500];logger.warning('Visual plan attempt %s: %s',attempt+1,feedback)
    plan=generic_visual(lesson,source_id,root=root)
    # Recover at scene granularity, preserving independently valid rich scenes.
    # Every candidate is validated against the real source with all other scenes
    # safely generic. No invalid field is silently repaired into false geometry.
    try:
        raw=hydrate_visual(json.loads(previous or '{}'),baseline)
        raw,numeric_notes=normalize_numeric_plan(raw,lesson)
        raw=ground_illustration_parts(raw,lesson)
        base=plan.model_dump(mode='json');sources=[]
        for index in range(len(lesson.scenes)):
            candidate=copy.deepcopy(plan.model_dump(mode='json'))
            try:
                candidate['scenes'][index]=raw['scenes'][index]
                accepted=validate_plan(VisualPlan.model_validate(candidate),lesson,source_id)
                base['scenes'][index]=accepted.model_dump(mode='json')['scenes'][index]
                sources.append('llm')
            except (ValueError,KeyError,IndexError,TypeError):sources.append('fallback')
            if sources[-1]=='fallback':
                try:
                    candidate['scenes'][index]=context_recovery(raw['scenes'][index])
                    accepted=validate_plan(VisualPlan.model_validate(candidate),lesson,source_id)
                    base['scenes'][index]=accepted.model_dump(mode='json')['scenes'][index]
                except (ValueError,KeyError,IndexError,TypeError):pass
        plan=validate_plan(VisualPlan.model_validate(base),lesson,source_id)
        return save_visual(plan,lesson,source='fallback',reason=feedback,root=root,scene_sources=sources,numeric_notes=numeric_notes)
    except (ValueError,KeyError,TypeError):
        return save_visual(plan,lesson,source='fallback',reason=feedback,root=root)
