import type {VisualProps} from "./contracts";
import {Label,Panel,Arrow,C} from "./Primitives";
import {activeIds,ease} from "./animation";

export function FunctionPlot({spec,labels,computed,beat,progress}:VisualProps){
 if(spec.data.kind!=="function_plot")return null;const d=spec.data;
 const box={x:200,y:215,w:850,h:285},px=(x:number)=>box.x+(x-d.x_min)/(d.x_max-d.x_min)*box.w,
 py=(y:number)=>box.y+box.h-(y-d.y_min)/(d.y_max-d.y_min)*box.h;
 const active=spec.beat_actions.filter(a=>a.beat_index===beat&&a.op==="plot_to_x").at(-1);
 const prior=spec.beat_actions.filter(a=>a.beat_index<beat&&a.op==="plot_to_x").at(-1);
 const from=prior?.value??d.x_min,to=active?.value??d.x_max,current=from+(to-from)*ease(progress);
 const samples=computed.samples||[];let previous=false;const paths:string[]=[];
 for(const p of samples){if(!p||p[0]>current){previous=false;continue;}
  paths.push(`${previous?"L":"M"}${px(p[0]).toFixed(3)} ${py(p[1]).toFixed(3)}`);previous=true;}
 const xZero=px(Math.max(d.x_min,Math.min(d.x_max,0))),yZero=py(Math.max(d.y_min,Math.min(d.y_max,0)));
 const clip=`plot-clip-${spec.scene_index}`;
 const point=samples.filter((p):p is [number,number]=>p!==null&&p[0]<=current).at(-1);
 const transition=spec.beat_actions.find(a=>a.op==="secant_to_tangent"&&a.beat_index<=beat);
 const transitionP=transition?(transition.beat_index<beat?1:progress):0;
 const tangent=computed.tangent,secant=transition&&computed.secant_path?.length
   ? computed.secant_path[Math.min(computed.secant_path.length-1,Math.floor(transitionP*(computed.secant_path.length-1)))]
   : computed.secant;
 return <g>
  <defs><clipPath id={clip}><rect x={box.x} y={box.y} width={box.w} height={box.h}/></clipPath></defs>
  <rect x={box.x} y={box.y} width={box.w} height={box.h} fill="#112c45" stroke="#6285a1"/>
  {Array.from({length:9},(_,i)=>{const x=d.x_min+i*(d.x_max-d.x_min)/8;return <g key={i}>
   <line x1={px(x)} y1={box.y} x2={px(x)} y2={box.y+box.h} stroke="#416079" opacity=".6"/>
   <text x={px(x)} y={box.y+box.h+24} textAnchor="middle" fill={C.muted} fontSize="17">{Number(x.toFixed(2))}</text>
  </g>;})}
  {Array.from({length:6},(_,i)=>{const y=d.y_min+i*(d.y_max-d.y_min)/5;return <g key={i}>
   <line x1={box.x} y1={py(y)} x2={box.x+box.w} y2={py(y)} stroke="#416079" opacity=".6"/>
   <text x={box.x-14} y={py(y)+6} textAnchor="end" fill={C.muted} fontSize="17">{Number(y.toFixed(2))}</text>
  </g>;})}
  <line x1={box.x} y1={yZero} x2={box.x+box.w} y2={yZero} stroke="#eff3fb" strokeWidth="2"/>
  <line x1={xZero} y1={box.y} x2={xZero} y2={box.y+box.h} stroke="#eff3fb" strokeWidth="2"/>
  <g clipPath={`url(#${clip})`}>
   {d.shade_interval&&<rect x={px(d.shade_interval[0])} y={box.y} width={px(d.shade_interval[1])-px(d.shade_interval[0])} height={box.h} fill={C.green} opacity=".12"/>}
   <path d={paths.join(" ")} fill="none" stroke={C.accent} strokeWidth="4"/>
   {[{line:secant,color:C.muted},{line:tangent,color:C.blue}].map(({line,color},i)=>line&&<line key={i}
    x1={px(d.x_min)} y1={py(line.y+line.slope*(d.x_min-line.x))}
    x2={px(d.x_max)} y2={py(line.y+line.slope*(d.x_max-line.x))} stroke={color} strokeWidth="2" strokeDasharray={i?undefined:"7 5"}/>)}
   {(computed.points||[]).filter(p=>p[0]<=current).map(([x,y],i)=><g key={i}>
    <circle cx={px(x)} cy={py(y)} r="6" fill={C.green}/>
    <text x={px(x)+10} y={py(y)-12} fill="white" fontSize="19">({x}, {Number(y.toFixed(3))})</text>
   </g>)}
   {point&&<circle cx={px(point[0])} cy={py(point[1])} r="8" fill="white" stroke={C.accent} strokeWidth="3"/>}
  </g>
  <Label text={labels[d.x_label_key]} id={d.x_label_key} x={640} y={559} width={700} size={22}/>
  <Label text={labels[d.y_label_key]} id={d.y_label_key} x={200} y={195} width={700} anchor="start" size={20} lines={1}/>
  <Label text={labels[d.curve_label_key]} id={d.curve_label_key} x={1090} y={230} width={180} size={21} color={C.accent}/>
 </g>;
}

export function NumberLine({spec,labels,beat}:VisualProps){
 if(spec.data.kind!=="number_line")return null;const d=spec.data,x=(v:number)=>160+(v-d.minimum)/(d.maximum-d.minimum)*970;
 return <g><Arrow a={{x:145,y:370}} b={{x:1150,y:370}}/>
  {Array.from({length:9},(_,i)=>{const n=d.minimum+i*(d.maximum-d.minimum)/8;return <g key={i}>
   <line x1={x(n)} x2={x(n)} y1="355" y2="385" stroke="white"/>
   <text x={x(n)} y="414" textAnchor="middle" fill={C.muted} fontSize="21">{Number(n.toFixed(3))}</text></g>;})}
  {d.intervals.map((interval,i)=><g key={i}>
   <line x1={x(interval.start)} x2={x(interval.end)} y1={325-i*24} y2={325-i*24} stroke={C.green} strokeWidth="7"/>
   {[{n:interval.start,closed:interval.start_closed},{n:interval.end,closed:interval.end_closed}].map((p,j)=><circle key={j} cx={x(p.n)} cy={325-i*24} r="9" fill={p.closed?C.green:"#101f3d"} stroke={C.green} strokeWidth="3"/>)}
  </g>)}
  {d.points.map((value,i)=>i<=beat&&<g key={i}>
   <circle cx={x(value)} cy="370" r={i===beat?10:7} fill={C.accent}/>
   <text x={x(value)} y={278-i%2*32} textAnchor="middle" fill={C.accent} fontSize="27">{value}</text>
   <line x1={x(value)} x2={x(value)} y1={285-i%2*32} y2="350" stroke={C.accent}/>
  </g>)}
  <Label text={labels[d.axis_label_key]} id={d.axis_label_key} x={640} y={510} width={900}/>
 </g>;
}

export function Chart({spec,labels}:VisualProps){
 if(spec.data.kind!=="data_chart")return null;const d=spec.data,all=d.series.flatMap(s=>s.values),max=Math.max(1,...all),min=Math.min(0,...all),span=max-min;
 const x0=170,y0=510,w=900,h=250;const y=(v:number)=>y0-(v-min)/span*h;
 if(d.chart==="pie"){
  const values=d.series[0].values,total=values.reduce((a,b)=>a+b,0);let angle=-Math.PI/2;
  return <g>{values.map((value,i)=>{const start=angle;angle+=value/total*Math.PI*2;
   const end=angle,large=end-start>Math.PI?1:0;const path=value===total?"":`M 515 375 L ${515+145*Math.cos(start)} ${375+145*Math.sin(start)} A 145 145 0 ${large} 1 ${515+145*Math.cos(end)} ${375+145*Math.sin(end)} Z`;
   return <g key={i}>{path?<path d={path} fill={[C.accent,C.blue,C.green,"#dba8e6"][i%4]} stroke="#101f3d" strokeWidth="3"/>:<circle cx="515" cy="375" r="145" fill={C.accent}/>}
    <Label text={`${labels[d.category_keys[i]]}: ${value} (${(value/total*100).toFixed(1)}%)`} id={d.category_keys[i]} x={790} y={260+i*41} anchor="start" width={360} size={23}/></g>;
  })}</g>;
 }
 return <g><line x1={x0} y1={y0} x2={x0+w} y2={y0} stroke="white"/>
  {Array.from({length:5},(_,i)=>{const value=min+i*span/4;return <g key={i}><line x1={x0} y1={y(value)} x2={x0+w} y2={y(value)} stroke="#55708b" opacity=".45"/>
   <text x={x0-10} y={y(value)+6} textAnchor="end" fill={C.muted} fontSize="18">{Number(value.toFixed(2))}</text></g>;})}
  {d.series.map((s,series)=>{const color=[C.accent,C.blue,C.green][series],step=w/d.category_keys.length;
   return <g key={series}>{d.chart==="line"&&<polyline points={s.values.map((v,i)=>`${x0+(i+.5)*step},${y(v)}`).join(" ")} fill="none" stroke={color} strokeWidth="4"/>}
    {s.values.map((v,i)=><g key={i}>{d.chart==="bar"?<rect x={x0+i*step+10+series*(step-20)/d.series.length} y={y(v)} width={(step-25)/d.series.length} height={y(0)-y(v)} fill={color}/>:<circle cx={x0+(i+.5)*step} cy={y(v)} r="6" fill={color}/>}
     <text x={x0+(i+.5)*step} y={y(v)-12-series*20} textAnchor="middle" fill="white" fontSize="20">{v}</text></g>)}
    <Label text={labels[s.label_key]} id={s.label_key} x={1070} y={225+series*28} width={220} size={18} color={color}/>
   </g>;})}
  {d.category_keys.map((key,i)=><Label key={i} text={labels[key]} id={key} x={x0+(i+.5)*w/d.category_keys.length} y={535} width={w/d.category_keys.length-10} size={20} lines={2}/>)}
  <Label text={labels[d.x_label_key]} id={d.x_label_key} x={640} y={205} width={700} size={20}/>
  <Label text={labels[d.y_label_key]} id={d.y_label_key} x={90} y={240} width={150} size={19}/>
 </g>;
}

export function Formula({spec,labels,computed,beat}:VisualProps){
 if(spec.data.kind!=="formula"&&spec.data.kind!=="equation_balance")return null;const d=spec.data;
 return <g><Label text={labels[d.expression_key]} id={d.expression_key} x={640} y={240} width={1050} size={34} color={C.accent}/>
  {d.step_keys.map((key,i)=>i<=beat&&<g key={key}>
   <Panel x={175} y={280+i*43} width={930} height={40} active={i===Math.min(beat,d.step_keys.length-1)}/>
   <Label text={computed.equation_steps?.[i]||labels[key]} id={key} x={640} y={308+i*43} width={880} size={27} lines={1}/>
  </g>)}
 </g>;
}

export function ForceMotion({spec,labels,computed,beat,progress}:VisualProps){
 if(spec.data.kind!=="force_motion")return null;const d=spec.data,active=activeIds(spec,beat);
 return <g><Label text={labels[d.schematic_label_key]} id={d.schematic_label_key} x={640} y={226} width={1000} size={24} color={C.accent}/>
  {d.mode==="force"?<>
   <line x1="150" y1="455" x2="1130" y2="455" stroke={C.muted} strokeWidth="4"/>
   <rect x="545" y="345" width="180" height="105" rx="12" fill="#3e6c88" stroke="#a3d9ea" strokeWidth="3"/>
   <text x="635" y="405" textAnchor="middle" fill="white" fontSize="28">{d.mass_kg} kg</text>
   {d.vectors.map((v,i)=>{const max=Math.max(1,...d.vectors.map(v=>Math.hypot(v.x,v.y))),factor=180/max;
    const e=spec.entities.find(e=>e.id===v.entity_id)!;const end={x:635+v.x*factor,y:395-v.y*factor};
    return <g key={i}><Arrow a={{x:635,y:395}} b={end} active={active.has(v.entity_id)} progress={progress}/>
     <Label text={`${labels[e.label_key]} ${Math.hypot(v.x,v.y).toFixed(1)} ${v.unit}`} id={e.label_key} x={end.x+(v.x>=0?45:-45)} y={end.y-20-i%2*22} width={250} size={22}/></g>;})}
   <text x="640" y="535" textAnchor="middle" fill={C.accent} fontSize="27">Fₓ = m aₓ · {computed.net_force?.[0]} N / {d.mass_kg} kg = {computed.acceleration?.[0]} m/s²</text>
   {computed.net_force?.[1]!==0&&<text x="640" y="565" textAnchor="middle" fill={C.accent} fontSize="23">Fᵧ = {computed.net_force?.[1]} N · aᵧ = {computed.acceleration?.[1]} m/s²</text>}
  </>:d.mode==="circuit"?<>
   <path d="M350 280H900V480H350V280" fill="none" stroke="#cbdce8" strokeWidth="5"/>
   <path d="M340 345V415M365 360V400" stroke={C.accent} strokeWidth="7"/>
   <rect x="570" y="262" width="120" height="36" fill="#101f3d" stroke={C.accent} strokeWidth="4"/>
   <Arrow a={{x:430,y:280}} b={{x:530,y:280}} active progress={progress}/>
   <text x="640" y="390" textAnchor="middle" fill="white" fontSize="29">I = {d.voltage_v} V / {d.resistance_ohm} Ω = {(d.voltage_v/d.resistance_ohm).toFixed(2)} A</text>
  </>:d.mode==="wave"?<>
   <line x1="170" y1="385" x2="1110" y2="385" stroke={C.muted}/>
   <polyline points={Array.from({length:181},(_,i)=>`${170+i*940/180},${385-Math.min(125,d.amplitude*60)*Math.sin(i/180*2*Math.PI*d.frequency_hz)}`).join(" ")} fill="none" stroke={C.blue} strokeWidth="4"/>
   <Arrow a={{x:240,y:385}} b={{x:240,y:385-Math.min(125,d.amplitude*60)}} active/>
   <text x="640" y="530" textAnchor="middle" fill={C.accent} fontSize="27">A = {d.amplitude} · f = {d.frequency_hz} Hz</text>
  </>:<>
   <path d="M180 420Q550 220 1080 420" stroke="#87abc2" fill="none" strokeWidth="5"/>
   <rect x={180+900*ease(progress)} y={382-110*Math.sin(Math.PI*ease(progress))} width="60" height="30" rx="8" fill={C.blue}/>
   <Arrow a={{x:180,y:485}} b={{x:1080,y:485}} active progress={progress}/>
   <text x="640" y="535" textAnchor="middle" fill={C.accent} fontSize="27">Δx = {d.displacement_m} m · Δt = {d.seconds} s · v = {(d.displacement_m/d.seconds).toFixed(2)} m/s</text>
  </>}
  {d.mode!=="force"&&spec.entities.map((e,i)=><Label key={e.id} text={labels[e.label_key]} id={e.label_key} x={230+i*860/Math.max(1,spec.entities.length-1)} y={255} width={180} size={20}/>)}
 </g>;
}

export function Reaction({spec,labels,progress}:VisualProps){
 if(spec.data.kind!=="reaction_equation")return null;const d=spec.data,all=[...d.reactants,...d.products];
 return <g><Arrow a={{x:570,y:355}} b={{x:710,y:355}} active progress={progress}/>
  {all.map((s,i)=>{const product=i>=d.reactants.length,index=product?i-d.reactants.length:i,count=product?d.products.length:d.reactants.length,
   x=(product?760:120)+(index+.5)*400/count;
   return <g key={i}><circle cx={x} cy="355" r="51" fill={product?"#365c4a":"#35506e"} stroke={C.accent} strokeWidth="2"/>
    <text x={x} y="365" textAnchor="middle" fill="white" fontSize="29">{s.coefficient} {s.formula}</text>
    <Label text={labels[s.label_key]} id={s.label_key} x={x} y={445} width={185} size={25}/>
    <text x={x} y="490" textAnchor="middle" fill={C.muted} fontSize="21">{s.state==="unspecified"?"":`(${s.state})`}</text></g>;})}
 </g>;
}

export function LabProcess({spec,labels,beat,progress}:VisualProps){
 if(spec.data.kind!=="lab_process")return null;const d=spec.data;
 const pouring=spec.beat_actions.filter(a=>a.op==="pour"&&a.beat_index<=beat).at(-1);
 const p=!pouring?0:pouring.beat_index<beat?1:ease(progress);
 const positions=Object.fromEntries(d.apparatus.map((a,i)=>[a.entity_id,220+i*800/Math.max(1,d.apparatus.length-1)]));
 return <g><Label text={labels[d.illustration_label_key]} id={d.illustration_label_key} x={640} y={230} width={1000} color={C.accent} size={23}/>
  {d.apparatus.map((a,i)=>{const x=positions[a.entity_id],isSource=a.entity_id===d.source_id,isTarget=a.entity_id===d.target_id,
   volume=a.volume_ml+(isTarget?1:isSource?-1:0)*d.transfer_ml*p,level=volume/a.capacity_ml*170,
   entity=spec.entities.find(e=>e.id===a.entity_id)!;
   const source=d.apparatus.find(a=>a.entity_id===d.source_id)!,fraction=source.volume_ml?d.transfer_ml*p/source.volume_ml:0;
   const solute=a.solute_units+(isTarget?source.solute_units*fraction:isSource?-a.solute_units*fraction:0);
   const shape=a.shape==='flask'?`M${x-30} 290V345L${x-80} 475Q${x-85} 500 ${x-55} 500H${x+55}Q${x+85} 500 ${x+80} 475L${x+30} 345V290`:
    a.shape==='pipette'?`M${x-17} 290V465L${x} 505L${x+17} 465V290`:
    a.shape==='test_tube'?`M${x-35} 290V465Q${x} 535 ${x+35} 465V290`:
    a.shape==='funnel'?`M${x-75} 300L${x-13} 390V490H${x+13}V390L${x+75} 300Z`:
    `M${x-70} 290V495H${x+70}V290`;
   return <g key={a.entity_id} data-entity-id={a.entity_id}>
    <defs><clipPath id={`vessel-${spec.scene_index}-${i}`}><path d={shape}/></clipPath></defs>
    <rect x={x-80} y={495-level} width="160" height={level} fill={C.blue} opacity=".7" clipPath={`url(#vessel-${spec.scene_index}-${i})`}/>
    <path d={shape} fill="none" stroke="#d2e5f2" strokeWidth="4"/>
    <Label text={labels[entity.label_key]} id={entity.label_key} x={x} y={275} width={250} size={24}/>
    <text x={x} y="535" textAnchor="middle" fill="white" fontSize="21">{volume.toFixed(1)} mL · {volume?(solute/volume).toFixed(3):0}</text>
   </g>;})}
  {p>0&&<Arrow a={{x:positions[d.source_id]+80,y:345}} b={{x:positions[d.target_id]-80,y:345}} active={p<1} progress={p} color={C.blue}/>}
 </g>;
}
