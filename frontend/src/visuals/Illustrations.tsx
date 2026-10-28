import type {VisualProps} from "./contracts";
import {Label,Arrow,C} from "./Primitives";
import {activeIds,introduced,clamp} from "./animation";
import type {Point} from "./layout";
const anchors:Record<string,Record<string,Point>>={
 human_digestive_system:{mouth:{x:630,y:223},esophagus:{x:630,y:280},stomach:{x:704,y:333},pancreas:{x:675,y:378},
  small_intestine:{x:635,y:440},large_intestine:{x:750,y:445},villi:{x:830,y:280},bloodstream:{x:790,y:500}},
 human_heart:{right_atrium:{x:580,y:310},right_ventricle:{x:585,y:440},left_atrium:{x:710,y:310},left_ventricle:{x:705,y:440},lungs:{x:825,y:235},body:{x:835,y:505}},
 plant_cell:{cell_wall:{x:460,y:260},membrane:{x:477,y:335},nucleus:{x:630,y:375},cytoplasm:{x:745,y:425},chloroplast:{x:760,y:290},vacuole:{x:585,y:280},mitochondrion:{x:525,y:455}},
 animal_cell:{membrane:{x:465,y:340},nucleus:{x:625,y:370},cytoplasm:{x:750,y:420},mitochondrion:{x:530,y:455}},
 leaf_photosynthesis:{leaf:{x:650,y:290},chloroplast:{x:710,y:310},roots:{x:635,y:500},stem:{x:640,y:420},air:{x:815,y:265},sugar:{x:805,y:450},oxygen:{x:805,y:355}},
};
function Digestive({absorption=0}:{absorption?:number}) {
 return <g strokeLinecap="round" strokeLinejoin="round">
  <path d="M600 212Q630 190 660 212L650 234H610Z" fill="#d98e9e" stroke="#ffd3d0" strokeWidth="3"/>
  <path d="M630 235V302Q630 323 665 321" stroke="#e7ac8b" strokeWidth="19" fill="none"/>
  <path d="M663 305C730 291 756 322 742 351C725 386 665 365 658 340Z" fill="#c56988" stroke="#ffb7c1" strokeWidth="4"/>
  <path d="M607 369Q623 355 639 366Q653 355 668 367Q685 356 702 369L725 381Q680 395 630 383Z" fill="#d6bb6a" stroke="#ffe49e" strokeWidth="3"/>
  <path d="M550 380H746V493H540V392" fill="none" stroke="#b988b7" strokeWidth="25"/>
  <path d="M572 395C680 375 711 414 574 416C530 438 727 437 580 458C550 477 682 480 710 463" fill="none" stroke="#efb581" strokeWidth="15"/>
  <path d="M640 494V539" stroke="#b988b7" strokeWidth="16"/>
  <rect x="775" y="230" width="110" height="100" rx="10" fill="#23435c" stroke="#9ec7de"/>
  <path d="M787 310V272Q797 244 807 272V307M814 310V272Q824 244 834 272V307M841 310V272Q851 244 861 272V310" stroke="#efb581" strokeWidth="8" fill="none"/>
  <path d="M797 310V275M824 310V275M851 310V275M790 317H864" stroke="#e47f86" strokeWidth="3" fill="none"/>
  {[797,824,851].map((x,i)=><circle key={x} cx={x-7+7*clamp(absorption*2-i*.25)} cy={253+48*clamp(absorption*2-i*.25)} r="3" fill="#fce49c"/>)}
  <path d="M720 495H840" stroke="#e47f86" strokeWidth="12"/>
 </g>;
}
function Heart() {
 return <g strokeWidth="4" stroke="#ffd0ca">
  <path d="M640 270C565 210 500 290 538 405Q560 485 640 535Q720 485 749 402C794 286 715 209 640 270Z" fill="#9f4e67"/>
  <path d="M640 277V507M541 358Q590 380 640 358Q696 382 750 358" fill="none"/>
  <path d="M568 265V216H602V269M685 265V212H720V275" fill="#579dcc"/>
  <path d="M750 302L816 244M745 446L826 491" fill="none" stroke="#85cae7" strokeWidth="12"/>
 </g>;
}
function Cell({plant}:{plant:boolean}) {
 return <g>
  {plant?<><rect x="455" y="220" width="360" height="310" rx="50" fill="#4b795f" stroke="#a6dda3" strokeWidth="12"/>
   <rect x="474" y="239" width="322" height="272" rx="40" fill="#32696c" stroke="#a0e4e3" strokeWidth="4"/>
   <ellipse cx="585" cy="280" rx="61" ry="32" fill="#81c8db" stroke="#d4f0f7" strokeWidth="3"/>
   {[285,470].map(y=><ellipse key={y} cx="756" cy={y} rx="29" ry="16" fill="#79b972" stroke="#c2e89f" strokeWidth="3"/>)}</>
   :<ellipse cx="635" cy="375" rx="182" ry="144" fill="#426c81" stroke="#92d9e7" strokeWidth="5"/>}
  <ellipse cx="630" cy="375" rx="54" ry="47" fill="#775b9e" stroke="#d8b1e7" strokeWidth="4"/>
  <circle cx="642" cy="371" r="14" fill="#c69adb"/>
  <ellipse cx="530" cy="455" rx="28" ry="15" fill="#dfaa77" stroke="#ffdfaf" strokeWidth="3"/>
  <path d="M511 451l9 9 9-13 8 13 10-10" stroke="#b97666" fill="none" strokeWidth="2"/>
 </g>;
}
function Leaf(){return <g strokeWidth="4"><path d="M640 500V332" stroke="#a0dba6"/>
 <path d="M640 363Q525 370 558 263Q645 262 640 363M642 334Q756 334 736 236Q645 244 642 334" fill="#459967" stroke="#a6e5aa"/>
 <path d="M640 500l-40 34m40-34 35 35m-35-35-3 43" stroke="#d7b17d"/>
 <ellipse cx="710" cy="310" rx="25" ry="15" fill="#81b85a" stroke="#d1e8a9"/>
 {[{x:815,y:265},{x:805,y:355},{x:805,y:450}].map((p,i)=><circle key={i} {...{cx:p.x,cy:p.y}} r="24" fill={i===2?"#c49748":"#6e9fbc"} stroke="#d5e9fa"/>)}</g>;}
export default function Illustrations({spec,labels,beat,progress}:VisualProps){
 const template=spec.template_id!;const points=anchors[template];const active=activeIds(spec,beat);
 const parts=spec.entities.filter(e=>e.anchor_id&&introduced(spec,e.id,beat));
 const allContext=spec.entities.filter(e=>!e.anchor_id&&introduced(spec,e.id,beat));
 const context=[...allContext.filter(e=>active.has(e.id)),...allContext.filter(e=>!active.has(e.id)).reverse()].slice(0,3);
 const focusedId=spec.beat_actions.find(a=>a.beat_index===beat&&a.op==='zoom_region')?.target_ids[0];
 const focus=parts.find(e=>e.id===focusedId)||parts.find(e=>active.has(e.id));
 const focusedPoint=focus?points[focus.anchor_id!]:null;
 const absorption=parts.some(e=>e.anchor_id==='villi'&&active.has(e.id))?progress:0;
 const artwork=()=>template==="human_digestive_system"?<Digestive absorption={absorption}/>:template==="human_heart"?<Heart/>:template==="leaf_photosynthesis"?<Leaf/>:<Cell plant={template==="plant_cell"}/>;
 const pointFor=(id:string)=>{const e=spec.entities.find(e=>e.id===id)!;
  const i=context.findIndex(e=>e.id===id);return points[e.anchor_id||""]||{x:430+Math.max(0,i)*Math.min(170,430/Math.max(1,context.length-1)),y:535};};
 const activeEdges=spec.relationships.filter(edge=>spec.beat_actions.some(a=>a.beat_index===beat&&a.op==='trace_path'&&a.target_ids[0]===edge.source&&a.target_ids[1]===edge.target));
 const clipId=`part-focus-${spec.scene_index}`;
 return <g data-visual-family="labelled_illustration">
  {artwork()}
  {spec.relationships.map((edge,i)=>{const a=spec.entities.find(e=>e.id===edge.source)!,b=spec.entities.find(e=>e.id===edge.target)!;
   const visible=(id:string)=>parts.some(e=>e.id===id)||context.some(e=>e.id===id);
   const show=visible(a.id)&&visible(b.id);
   return show?<g key={i}><Arrow a={pointFor(a.id)} b={pointFor(b.id)} progress={progress} active={activeEdges.includes(edge)}/></g>:null;})}
  {parts.map((entity,i)=>{const p=pointFor(entity.id),y=220+i*Math.min(48,300/Math.max(1,parts.length-1));
   return <g key={entity.id} data-entity-id={entity.id} data-active={active.has(entity.id)}>
    <path d={`M 352 ${y+5} H ${375+i*5} L ${p.x} ${p.y}`} fill="none" stroke={active.has(entity.id)?C.accent:C.muted} strokeWidth={active.has(entity.id)?3:1}/>
    <circle cx={p.x} cy={p.y} r={active.has(entity.id)?12:6} fill={C.accent} opacity={active.has(entity.id)?1:.65}/>
    <Label text={labels[entity.label_key]} id={entity.label_key} x={100} y={y} anchor="start" width={245} size={23} lines={2} color={active.has(entity.id)?C.accent:C.ink}/>
   </g>;})}
  {context.map(entity=>{const p=pointFor(entity.id);return <g key={entity.id} data-entity-id={entity.id} data-active={active.has(entity.id)}>
   <rect x={p.x-72} y={p.y-22} width="144" height="53" rx="10" fill={C.panel} stroke={active.has(entity.id)?C.accent:C.muted}/>
   <Label text={labels[entity.label_key]} id={entity.label_key} x={p.x} y={p.y-1} width={136} size={18} lines={2}/>
  </g>;})}
  {focusedPoint&&spec.data.kind==='labelled_illustration'&&spec.data.zoom==='focused_part'&&<g data-focus-anchor={focus!.anchor_id}>
   <rect x="907" y="230" width="285" height="285" rx="16" fill="#112d45" stroke={C.accent} strokeWidth="2"/>
   <defs><clipPath id={clipId}><rect x="916" y="238" width="267" height="268" rx="10"/></clipPath></defs>
   <g clipPath={`url(#${clipId})`}><g transform={`translate(1049 372) scale(${focus!.anchor_id==='villi'?2.3:1.8}) translate(${-focusedPoint.x} ${-focusedPoint.y})`}>{artwork()}</g></g>
   <Label text={labels[focus!.label_key]} x={1049} y={214} width={285} size={23} lines={1} color={C.accent}/>
   <path d={`M ${focusedPoint.x+14} ${focusedPoint.y} L 897 372`} stroke={C.accent} strokeDasharray="5 6" opacity=".6" fill="none"/>
  </g>}
  {activeEdges.slice(0,1).map(edge=><Label key={edge.label_key} text={labels[edge.label_key]} x={1049} y={545} width={285} size={20} lines={1} color={C.accent}/>)}
 </g>;
}
