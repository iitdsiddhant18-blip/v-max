import type {VisualProps} from "./contracts";
import {Label,Panel,Arrow,C} from "./Primitives";
import {nodePositions,boxEdgePoints} from "./layout";
import {activeIds,introduced,selectedState,ease} from "./animation";

export function ConceptMap({spec,labels,beat,progress}:VisualProps){
 const positions=nodePositions(spec.entities.length,"layout" in spec.data?spec.data.layout:"row");
 const byId=Object.fromEntries(spec.entities.map((e,i)=>[e.id,positions[i]]));const active=activeIds(spec,beat);
 const current=spec.beat_actions.filter(a=>a.beat_index===beat);
 const focusedEdge=spec.relationships.find(edge=>current.some(a=>
  (a.target_ids.length===2&&a.target_ids[0]===edge.source&&a.target_ids[1]===edge.target)
  ||(a.target_ids.length===1&&a.target_ids[0]===edge.target)));
 return <g>{spec.relationships.map((edge,i)=>{const a=byId[edge.source],b=byId[edge.target];
  if(!introduced(spec,edge.source,beat)||!introduced(spec,edge.target,beat))return null;
  const points=boxEdgePoints(a,b);
  const reverse=spec.relationships.some(e=>e.source===edge.target&&e.target===edge.source);
  if(reverse){const sign=edge.source<edge.target?-1:1;points.forEach(p=>p.y+=sign*30);}
  return <g key={i}><Arrow a={points[0]} b={points[1]} active={focusedEdge===edge} progress={progress}/></g>;})}
  {spec.entities.map((e,i)=>introduced(spec,e.id,beat)&&<g key={e.id} data-entity-id={e.id} data-active={active.has(e.id)}>
   <Panel x={positions[i].x-94} y={positions[i].y-48} width={188} height={105} active={active.has(e.id)}/>
   <Label text={labels[e.label_key]} id={e.label_key} x={positions[i].x} y={positions[i].y-8} width={166} size={25}/>
  </g>)}
  {focusedEdge&&<Label text={labels[focusedEdge.label_key]} id={focusedEdge.label_key} x={640} y={553} width={1060} size={22} color={C.accent} lines={1}/>}
 </g>;
}

export function Comparison({spec,labels,beat}:VisualProps){
 if(spec.data.kind!=="comparison"&&spec.data.kind!=="table")return null;const d=spec.data;
 const width=1100/d.column_keys.length,rowHeight=270/d.rows.length;
 return <g>{d.column_keys.map((key,col)=><g key={key}>
  <Panel x={90+col*width} y={205} width={width-10} height={345}/>
  <Label text={labels[key]} id={key} x={90+(col+.5)*width} y={240} width={width-40} color={C.accent} size={27}/>
  {d.rows.map((row,i)=><g key={i}>
   {Math.min(beat,d.rows.length-1)===i&&<rect x={100+col*width} y={270+i*rowHeight} width={width-30} height={rowHeight-5} rx="10" fill="#315a73"/>}
   <Label text={labels[row[col]]} id={row[col]} x={90+(col+.5)*width} y={295+i*rowHeight} width={width-50} size={24} lines={3}/>
  </g>)}
 </g>)}</g>;
}

export function Timeline({spec,labels,beat}:VisualProps){
 if(spec.data.kind!=="timeline")return null;const active=activeIds(spec,beat),events=spec.data.events;
 return <g><line x1="145" y1="370" x2="1130" y2="370" stroke="#84a9c5" strokeWidth="4"/>
  {events.map((event,i)=>{const entity=spec.entities.find(e=>e.id===event.entity_id)!;const x=150+i*970/Math.max(1,events.length-1),upper=i%2===0;
   return introduced(spec,entity.id,beat)&&<g key={entity.id} data-entity-id={entity.id} data-active={active.has(entity.id)}>
    <circle cx={x} cy="370" r={active.has(entity.id)?13:8} fill={C.accent}/>
    <line x1={x} y1="370" x2={x} y2={upper?305:420} stroke={C.accent}/>
    <Label text={labels[event.time_label_key]} id={event.time_label_key} x={x} y={upper?265:450} width={170} size={20} color={C.accent}/>
    <Label text={labels[entity.label_key]} id={entity.label_key} x={x} y={upper?298:485} width={170} size={23}/>
   </g>;})}
 </g>;
}

export function Algorithm({spec,labels,computed,beat,progress}:VisualProps){
 if(spec.data.kind!=="algorithm_state")return null;const d=spec.data,states=computed.states||[];
 const target=Math.min(selectedState(spec,beat),Math.max(0,states.length-1));
 const prior=Math.min(selectedState(spec,beat-1),target);
 const span=target-prior,position=span*progress;
 const index=span?Math.min(target,prior+Math.max(1,Math.ceil(position))):target;
 const moveProgress=span?(position===0?0:position-Math.max(0,Math.ceil(position)-1)):1;
 const state=states[index],prev=states[Math.max(0,index-1)];
 if(!state)return null;
 if(d.algorithm==="binary_search"){
  const count=d.values.length,width=1000/count;return <g>
   <Label text={labels[d.state_label_key]} id={d.state_label_key} x={640} y={230} width={950} color={C.accent}/>
   {d.values.map((value,i)=><g key={i} opacity={i>=(state.low??0)&&i<=(state.high??count-1)?1:.22}>
    <Panel x={130+i*width} y={330} width={width-5} height={75} active={state.mid===i}/>
    <text x={130+(i+.5)*width} y="378" textAnchor="middle" fill="white" fontSize="30">{value}</text>
    <text x={130+(i+.5)*width} y="430" textAnchor="middle" fill={C.muted} fontSize="20">{i}</text>
   </g>)}
   {[state.low,state.mid,state.high].map((position,i)=>position!=null&&position>=0&&position<count&&<g key={i}>
    <Arrow a={{x:130+(position+.5)*width,y:280-i*16}} b={{x:130+(position+.5)*width,y:325}} active/>
    <Label text={labels[d.pointer_keys[i]]} x={130+(position+.5)*width} y={255-i*21} width={150} size={19}/>
   </g>)}
  </g>;
 }
 const rods=state.rods!,old=prev?.rods||rods;const centers={a:300,b:640,c:980};
 function diskPosition(rods:Record<string,number[]>,disk:number){
  for(const [rod,values] of Object.entries(rods)){const i=values.indexOf(disk);if(i>=0)return {x:centers[rod as keyof typeof centers],y:500-i*34};}
  return {x:300,y:500};
 }
 return <g>
  <Label text={`${labels[d.state_label_key]} ${state.move??index} / ${states.length-1}`} id={d.state_label_key} x={640} y={225} width={850} color={C.accent}/>
  {Object.entries(centers).map(([id,x],i)=><g key={id}><rect x={x-6} y="278" width="12" height="238" rx="6" fill="#a3b5c6"/>
   <rect x={x-135} y="520" width="270" height="12" rx="5" fill="#9db0c4"/>
   <Label text={labels[d.pointer_keys[i]]} id={d.pointer_keys[i]} x={x} y={565} width={230} size={25}/></g>)}
  {Array.from({length:d.disks},(_,i)=>d.disks-i).map(disk=>{const end=diskPosition(rods,disk),start=diskPosition(old,disk),moving=state.disk===disk;
   const p=ease(moveProgress),point=!moving?end:p<.33?{x:start.x,y:start.y+(255-start.y)*p/.33}:p<.67?{x:start.x+(end.x-start.x)*(p-.33)/.34,y:255}:{x:end.x,y:255+(end.y-255)*(p-.67)/.33};
   return <g key={disk} data-disk={disk}><rect x={point.x-(45+disk*22)} y={point.y-20} width={90+disk*44} height="28" rx="8" fill={[C.blue,C.accent,C.green,"#dba8e6"][disk-1]} stroke="#eef5ff" strokeWidth="2"/>
    <text x={point.x} y={point.y} fill="#10243b" fontSize="19" textAnchor="middle">{disk}</text></g>;})}
  {state.source&&state.target&&<Arrow a={{x:centers[state.source as keyof typeof centers],y:270}} b={{x:centers[state.target as keyof typeof centers],y:270}} active progress={progress}/>}
 </g>;
}

export function CodeTrace({spec,labels,computed,beat}:VisualProps){
 if(spec.data.kind!=="code_trace")return null;const d=spec.data,states=computed.states||[];
 const chosen=Math.min(selectedState(spec,beat),Math.max(0,states.length-1));const state=states[chosen];
 const lines=d.code.split("\n"),line=state?.line||computed.explanation_lines?.[beat]||Math.min(beat+1,lines.length);
 return <g><Panel x={90} y={205} width={735} height={350}/>
  {lines.map((text,i)=><g key={i}>
   {i+1===line&&<rect x="102" y={214+i*25} width="708" height="25" fill="#315b76"/>}
   {i+1===line&&<path d={`M108 ${225+i*25}l12-7v14z`} fill={C.accent}/>}
   <text x="132" y={235+i*25} fill={C.muted} fontSize="17">{i+1}</text>
   <text x="170" y={235+i*25} fill="white" fontSize={Math.min(22,610/Math.max(1,text.length)/.62)} fontFamily="Consolas,monospace" xmlSpace="preserve">{text}</text>
  </g>)}
  <Panel x={845} y={205} width={345} height={350}/>
  <Label text={labels[d.variables_label_key]} id={d.variables_label_key} x={865} y={239} anchor="start" width={300} color={C.accent} size={22}/>
  {Object.entries(state?.variables||{}).slice(0,5).map(([name,value],i)=><text key={name} x="865" y={276+i*28} fill="white" fontSize="21">{name} = {JSON.stringify(value)}</text>)}
  <Label text={labels[d.output_label_key]} id={d.output_label_key} x={865} y={442} anchor="start" width={300} color={C.accent} size={22}/>
  <Label text={(state?.output||[]).join(", ")||labels[d.status_label_key]} x={865} y={480} anchor="start" width={300} size={22}/>
 </g>;
}
