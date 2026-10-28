"""Topic-neutral evidence rubric evaluated from the proposed teaching facts."""
import re
from pydantic import Field
from .visual_schema import Frozen


class Complexity(Frozen):
    prerequisite: int=Field(ge=0,le=2)
    causal_steps: int=Field(ge=0,le=2)
    formal_reasoning: int=Field(ge=0,le=2)
    worked_example: int=Field(ge=0,le=2)
    evidence: tuple[str,...]
    target_seconds: int=Field(ge=30,le=90)


def assess_complexity(lesson, request, semantic_draft=None):
    scenes=lesson.scenes; facts=[f for s in scenes[1:-1] for f in s.items]
    text=' '.join(facts)
    prerequisite=min(2,sum(bool(re.search(r'\b'+term+r'\b',text,re.I)) for term in ('requires','before','assume','depends')))
    steps=0 if len(facts)<=3 else 1 if len(facts)<=7 else 2
    numeric=len(re.findall(r'\b\d+(?:\.\d+)?\b|[=²³∑]',text))
    formal=min(2,(numeric>=2)+(numeric>=6))
    examples=sum(bool(re.search(r'example|predict|calculate|trace|substitut|suppose|case',s.heading+' '+s.narration,re.I)) for s in scenes)
    worked=min(2,examples)
    objects=[]
    if semantic_draft:
        mechanisms=semantic_draft.get('explanations',[])
        objects=sorted({b[k] for section in mechanisms for b in section.get('beats',[])
                        for k in ('source_label','target_label')})
        relationships={b['relation_label'] for section in mechanisms for b in section.get('beats',[])}
        prerequisite=max(prerequisite,0 if len(objects)<=3 else 1 if len(objects)<=6 else 2)
        steps=max(steps,0 if len(relationships)<=1 else 1 if len(relationships)<=3 else 2)
        case_beats=len(semantic_draft.get('worked_example',{}).get('beats',[]))
        worked=max(worked,0 if case_beats==0 else 1 if case_beats<=2 else 2)
    total=prerequisite+steps+formal+worked
    target=40 if total<=2 else 57 if total<=5 else 77
    if request.duration_mode=='manual':target=request.target_seconds
    return Complexity(prerequisite=prerequisite,causal_steps=steps,formal_reasoning=formal,
        worked_example=worked,target_seconds=target,evidence=(
            f'Prerequisite dependency signals: {prerequisite}; explicit objects: {", ".join(objects)}',f'{len(facts)} mechanism facts',
            f'{numeric} explicit numeric/symbolic terms',f'{examples} example/prediction scenes'))
