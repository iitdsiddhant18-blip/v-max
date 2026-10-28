"""Regenerate canonical serialized visual types, schema and controlled examples."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from backend.app.visual_schema import VisualPlan,VisualScene
from backend.tests.test_visual_schema import family_specs,scene_for


def ts(node):
    if '$ref' in node:return node['$ref'].split('/')[-1]
    if 'const' in node:return json.dumps(node['const'])
    if 'enum' in node:return ' | '.join(json.dumps(v) for v in node['enum'])
    for union in ('anyOf','oneOf'):
        if union in node:return ' | '.join(dict.fromkeys(ts(v) for v in node[union]))
    kind=node.get('type')
    if kind=='null':return 'null'
    if kind=='string':return 'string'
    if kind in ('number','integer'):return 'number'
    if kind=='boolean':return 'boolean'
    if kind=='array':
        if 'prefixItems' in node:return '['+', '.join(ts(v) for v in node['prefixItems'])+']'
        return '('+ts(node.get('items',{}))+')[]'
    if kind=='object':
        if 'properties' in node:return '{\n'+'\n'.join('  '+key+': '+ts(value)+';' for key,value in node['properties'].items())+'\n}'
        return 'Record<string, '+ts(node.get('additionalProperties',{}))+'>'
    return 'unknown'


def main():
    schema=VisualPlan.model_json_schema()
    file=ROOT/'frontend/src/visuals/contracts.ts'
    computed='export interface TraceState'+file.read_text(encoding='utf-8').split('export interface TraceState',1)[1]
    definitions=schema['$defs']
    content='// Generated from backend/app/visual_schema.py JSON schema. Canonical serialized values include defaults.\n\n'
    content+='\n\n'.join('export type '+name+' = '+ts(definition)+';' for name,definition in definitions.items())
    content+='\n\nexport type VisualPlan = '+ts(schema)+';\n\n'+computed
    file.write_text(content,encoding='utf-8')
    (ROOT/'docs/visual_schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    examples={name:VisualScene.model_validate(scene_for(name)).model_dump(mode='json') for name in family_specs()}
    (ROOT/'docs/visual_examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Regenerated canonical TypeScript, JSON schema and',len(examples),'validated controlled examples')


if __name__=='__main__':main()
