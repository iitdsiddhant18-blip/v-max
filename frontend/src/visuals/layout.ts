export type Point={x:number;y:number};
export const CONTENT={left:90,right:1190,top:205,bottom:550};
export function nodePositions(count:number,layout="row"):Point[] {
  if(layout==="cycle")return Array.from({length:count},(_,i)=>({
    x:640+410*Math.cos(-Math.PI/2+i*2*Math.PI/count),y:380+137*Math.sin(-Math.PI/2+i*2*Math.PI/count)}));
  const columns=count<=4?count:Math.ceil(count/2),rows=Math.ceil(count/columns);
  return Array.from({length:count},(_,i)=>({x:130+(i%columns+.5)*1020/columns,
    y:rows===1?355:280+Math.floor(i/columns)*195}));
}
export function edgePoints(a:Point,b:Point,radius=55):[Point,Point] {
  const length=Math.max(1,Math.hypot(b.x-a.x,b.y-a.y));
  return [{x:a.x+(b.x-a.x)*radius/length,y:a.y+(b.y-a.y)*radius/length},
    {x:b.x-(b.x-a.x)*radius/length,y:b.y-(b.y-a.y)*radius/length}];
}
export function boxEdgePoints(a:Point,b:Point):[Point,Point] {
  const dx=b.x-a.x,dy=b.y-a.y;
  const scale=Math.min(.45,1/Math.max(Math.abs(dx)/102,Math.abs(dy)/62,.001));
  return [{x:a.x+dx*scale,y:a.y+dy*scale},{x:b.x-dx*scale,y:b.y-dy*scale}];
}
