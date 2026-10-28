let canvas: HTMLCanvasElement | undefined;
const font='"Noto Sans", "Noto Sans Devanagari", "Noto Sans Kannada", sans-serif';
export async function ensureVisualFonts() {
  await Promise.all([
    document.fonts.load('400 24px "Noto Sans"','Input output −2 3.5'),
    document.fonts.load('700 42px "Noto Sans"','Teaching'),
    document.fonts.load('400 24px "Noto Sans Devanagari"','प्रारंभिक अवस्था'),
    document.fonts.load('700 42px "Noto Sans Devanagari"','शिक्षा'),
    document.fonts.load('400 24px "Noto Sans Kannada"','ಆರಂಭಿಕ ಸ್ಥಿತಿ'),
    document.fonts.load('700 42px "Noto Sans Kannada"','ಶಿಕ್ಷಣ'),
  ]);
  await document.fonts.ready;
}
export function textWidth(text:string,size:number) {
  if(typeof document==="undefined")return text.length*size*.65;
  canvas ||= document.createElement("canvas");
  const ctx=canvas.getContext("2d");
  if(!ctx)return text.length*size*.65;
  ctx.font=`${size}px ${font}`;
  return ctx.measureText(text).width;
}
export function fitText(text:string,width:number,maxSize=26,maxLines=3) {
  const segmenter=new Intl.Segmenter(undefined,{granularity:"grapheme"});
  function wrap(size:number) {
    const lines:string[]=[];let line="";
    for(const word of text.split(/\s+/)) {
      if(textWidth(line?`${line} ${word}`:word,size)<=width) {line=line?`${line} ${word}`:word;continue;}
      if(line){lines.push(line);line="";}
      if(textWidth(word,size)<=width){line=word;continue;}
      for(const {segment} of segmenter.segment(word)) {
        if(line&&textWidth(line+segment,size)>width){lines.push(line);line="";}
        line+=segment;
      }
    }
    if(line)lines.push(line);return lines;
  }
  for(let size=maxSize;size>=14;size-=1){const lines=wrap(size);if(lines.length<=maxLines)return {size,lines};}
  // Preserve required text: callers reserve/reflow all returned lines, no ellipsis.
  return {size:14,lines:wrap(14)};
}
