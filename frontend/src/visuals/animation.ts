import type { VisualScene, BeatAction } from "./contracts";
export const clamp = (x: number) => Math.max(0, Math.min(1, x));
export const ease = (x: number) => { const p=clamp(x); return p*p*(3-2*p); };
export function actionProgress(action: BeatAction, beat: number, progress: number) {
  return action.beat_index < beat ? 1 : action.beat_index === beat ? clamp(progress) : 0;
}
export function activeIds(spec: VisualScene, beat: number) {
  return new Set(spec.beat_actions.filter(a=>a.beat_index===beat).flatMap(a=>a.target_ids));
}
export function introduced(spec: VisualScene, id: string, beat: number) {
  return spec.entities.find(e=>e.id===id)?.role === "context"
    || spec.beat_actions.some(a=>a.target_ids.includes(id) && a.beat_index<=beat);
}
export function selectedState(spec: VisualScene, beat: number) {
  return spec.beat_actions.filter(a=>a.beat_index<=beat && a.op==="set_state")
    .reduce((n,a)=>a.state_index ?? n,0);
}
