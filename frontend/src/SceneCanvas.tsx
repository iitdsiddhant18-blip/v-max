import type { SampleTimeline, Scene } from "./types";
import DynamicSceneContent, { GeneratedHeading } from "./DynamicSceneContent";

function clamp(value: number, minimum = 0, maximum = 1): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function wrapWords(text: string, length = 60): string[] {
  const lines: string[] = [];
  let line = "";
  for (const word of text.split(/\s+/)) {
    if (line && `${line} ${word}`.length > length) {
      lines.push(line);
      line = word;
    } else {
      line = line ? `${line} ${word}` : word;
    }
  }
  if (line) lines.push(line);
  return lines.slice(0, 3);
}

function Content({ scene, progress, hindi }: { scene: Scene; progress: number; hindi: boolean }) {
  if (scene.type === "title_card") {
    return (
      <g>
        <text x="640" y="318" textAnchor="middle" fill="#ffda76" fontSize="56" fontWeight="700">
          {scene.heading}
        </text>
        <text x="640" y="391" textAnchor="middle" fill="#dce5ff" fontSize="29">
          {scene.subtitle || "Learn it one step at a time"}
        </text>
      </g>
    );
  }

  if (scene.type === "code_walkthrough") {
    const lines = (scene.code || "").split("\n");
    return (
      <g>
        <rect x="110" y="172" width="1060" height="360" rx="26" fill="#0c1a32" stroke="#5876a7" />
        {lines.map((line, index) => (
          <g key={index}>
            {scene.highlight_lines.includes(index + 1) && (
              <rect x="138" y={217 + index * 91} width="1000" height="67" rx="12"
                fill="#204866" />
            )}
            <text x="166" y={266 + index * 91} fontFamily="Consolas, monospace"
              fontSize="37" fill="#f7f9ff" xmlSpace="preserve">
              {line}
            </text>
          </g>
        ))}
        <text x="166" y="457" fill="#c5dcff" fontSize="27">
          {hindi ? "रेंज तीन के मान" : "Values from range(3)"}
        </text>
        {[0, 1, 2].map((value, index) => (
          <g key={value}>
            <rect x={630 + index * 165} y="407" width="120" height="76" rx="16"
              fill="#1c4669" stroke="#78d5f1" strokeWidth="2" />
            <text x={690 + index * 165} y="457" textAnchor="middle"
              fill="#ffda76" fontSize="35">{value}</text>
          </g>
        ))}
      </g>
    );
  }

  if (scene.type === "diagram") {
    // This fixed sample narrates taking a value and then running print(i).
    // Show both operations together; equal-time reveals are not speech alignment.
    const items = scene.items.slice(0, 3);
    return (
      <g>
        {items.map((item, index) => {
          const x = 265 + index * 360;
          const value = item.split("=").pop()?.trim() || "";
          return (
            <g key={index}>
              <rect x={x - 140} y="215" width="280" height="305" rx="22"
                fill="#1c4669" stroke="#78d5f1" strokeWidth="3" />
              <text x={x} y="253" fill="#c5dcff" fontSize="23" textAnchor="middle">
                {hindi ? "अगला मान लें" : "Take the next value"}
              </text>
              <text x={x} y="301" fill="white" fontSize="34" textAnchor="middle">{item}</text>
              <path d={`M ${x} 318 v 29 m -8 -10 l 8 10 l 8 -10`}
                fill="none" stroke="#ffcf68" strokeWidth="3" />
              <text x={x} y="390" fill="white" fontSize="32" textAnchor="middle"
                fontFamily="Consolas, monospace">print(i)</text>
              <text x={x} y="435" fill="#c5dcff" fontSize="23" textAnchor="middle">
                {hindi ? "प्रिंट का निर्देश चलाएँ" : "Run the print instruction"}
              </text>
              <text x={x} y="484" fill="#ffda76" fontSize="30" textAnchor="middle">
                {hindi ? "आउटपुट" : "Output"}: {value}
              </text>
              {index < items.length - 1 && (
                <g fill="#ffcf68" stroke="#ffcf68" strokeWidth="4">
                  <line x1={x + 150} y1="365" x2={x + 205} y2="365" />
                  <path d={`M ${x + 205} 365 l -15 -10 v 20 z`} />
                </g>
              )}
            </g>
          );
        })}
      </g>
    );
  }

  const count = Math.max(1, Math.ceil(progress * scene.items.length));
  return (
    <g>
      {scene.items.map((item, index) => (
        <g key={index} opacity={index < count ? 1 : 0.16}>
          <circle cx="195" cy={223 + index * 100} r="27" fill="#ffc95e" />
          <text x="195" y={233 + index * 100} textAnchor="middle"
            fontSize="27" fontWeight="700" fill="#10223f">{index + 1}</text>
          <text x="255" y={233 + index * 100} fontSize="33" fill="#f7f9ff">{item}</text>
        </g>
      ))}
    </g>
  );
}

export default function SceneCanvas({ timeline, time }: {
  timeline: SampleTimeline; time: number;
}) {
  const t = clamp(time, 0, timeline.total_seconds);
  let index = 0;
  for (let i = 1; i < timeline.scenes.length; i += 1) {
    if (t >= timeline.scenes[i].start_seconds) index = i;
  }
  const entry = timeline.scenes[index];
  const scene = timeline.lesson.scenes[index];
  const semanticScene = timeline.semantic_lesson?.scenes[index];
  const local = t - entry.start_seconds;
  const progress = clamp(local / Math.max(entry.audio_seconds, 0.001));
  const cue = entry.cues?.find(c => local >= c.start_seconds && local < c.end_seconds)
    || entry.cues?.[entry.cues.length - 1];
  const cueProgress = cue ? clamp((local - cue.start_seconds) / Math.max(.001, cue.end_seconds - cue.start_seconds)) : 0;
  const captions = wrapWords(timeline.kind === "generated" ? cue?.text || scene.narration : scene.narration,
    timeline.kind === "generated" ? 78 : 60);

  return (
    <svg id="lesson-stage" data-time={t.toFixed(6)} width="1280" height="720"
      viewBox="0 0 1280 720" role="img" aria-label={`Scene ${index + 1}: ${scene.heading}`}
      style={{ display: "block", width: "100%", height: "auto",
        fontFamily: '"Noto Sans", "Noto Sans Devanagari", "Noto Sans Kannada", sans-serif' }}>
      <rect width="1280" height="720" fill="#101f3d" />
      <rect x="0" y="0" width={1280 * clamp(t / timeline.total_seconds)} height="10" fill="#ffca63" />
      <text x="80" y="94" fill="#ffcf68" fontSize="26" fontWeight="700">BLU VISUAL TEACHER</text>
      {scene.type !== "title_card" && (
        timeline.kind === "generated" ? <GeneratedHeading heading={scene.heading} />
          : <text x="85" y="152" fill="white" fontSize="42" fontWeight="700">{scene.heading}</text>
      )}
      {timeline.kind === "generated"
        ? <DynamicSceneContent scene={scene} semanticScene={semanticScene} progress={progress} cue={cue} cueProgress={cueProgress} language={timeline.language} />
        : <Content scene={scene} progress={progress} hindi={timeline.language === "hi"} />}
      <rect x="0" y="579" width="1280" height="141" fill="#071226" />
      {captions.map((line, i) => (
        <text key={i} data-caption={timeline.kind === "generated" ? "true" : undefined}
          x="640" y={622 + i * 35} textAnchor="middle"
          fill="white" fontSize={timeline.kind === "generated" ? 24 : 27}>{line}</text>
      ))}
      <text x="1190" y="98" fill="#b9cbef" fontSize="22" textAnchor="end">
        {index + 1} / {timeline.scenes.length}
      </text>
    </svg>
  );
}
