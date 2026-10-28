import {fitText} from "./textLayout";
import type {Point} from "./layout";
export const C={ink:"#eaf4ff",muted:"#aac2d9",accent:"#ffd278",blue:"#70ccf0",green:"#9ee0b6",panel:"#17344d"};
export function Label({text,x,y,width=210,size=25,anchor="middle",color=C.ink,lines=3,id}: {
  text:string;x:number;y:number;width?:number;size?:number;anchor?:"middle"|"start"|"end";color?:string;lines?:number;id?:string;
}) {
  const fit=fitText(text,width,size,lines);
  return <text data-label-key={id} x={x} y={y} textAnchor={anchor} fill={color} fontSize={fit.size}>
    {fit.lines.map((line,i)=><tspan key={i} x={x} dy={i?fit.size*1.32:0}>{line}</tspan>)}
  </text>;
}
export function Arrow({a,b,progress=1,active=false,color=C.accent}: {
  a:Point;b:Point;progress?:number;active?:boolean;color?:string;
}) {
  const angle=Math.atan2(b.y-a.y,b.x-a.x),p=Math.max(0,Math.min(1,progress));
  return <g stroke={color} fill={color} opacity={active?1:.45}>
    <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} strokeWidth={active?4:2}/>
    <path d={`M ${b.x} ${b.y} L ${b.x-13*Math.cos(angle-.5)} ${b.y-13*Math.sin(angle-.5)} L ${b.x-13*Math.cos(angle+.5)} ${b.y-13*Math.sin(angle+.5)} Z`} />
    {active&&<circle cx={a.x+(b.x-a.x)*p} cy={a.y+(b.y-a.y)*p} r="7" fill="white" strokeWidth="2"/>}
  </g>;
}
export function Panel({x,y,width,height,active=false}: {x:number;y:number;width:number;height:number;active?:boolean}) {
  return <rect x={x} y={y} width={width} height={height} rx="18" fill={C.panel} stroke={active?C.accent:"#50718c"} strokeWidth={active?3:1}/>;
}
