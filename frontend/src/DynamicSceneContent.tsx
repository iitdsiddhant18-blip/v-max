import type { NarrationCue, Scene } from "./types";

function tr(key: string, lang?: string): string {
  if (lang === "hi") {
    const dict: Record<string, string> = {
      "Without light": "प्रकाश के बिना",
      "With light": "प्रकाश के साथ",
      "No new sugar": "कोई नई शर्करा नहीं",
      "New sugar": "नई शर्करा",
      "Same water and carbon dioxide • compare light": "समान पानी और कार्बन डाइऑक्साइड • प्रकाश की तुलना करें",
      "Plant growth": "पौधों की वृद्धि",
      "Example data / trace": "उदाहरण डेटा / ट्रेस",
      "Let's learn, one step at a time": "आइए सीखें, एक समय में एक कदम",
    };
    return dict[key] || key;
  }
  if (lang === "kn") {
    const dict: Record<string, string> = {
      "Without light": "ಬೆಳಕಿಲ್ಲದೆ",
      "With light": "ಬೆಳಕಿನೊಂದಿಗೆ",
      "No new sugar": "ಹೊಸ ಸಕ್ಕರೆ ಇಲ್ಲ",
      "New sugar": "ಹೊಸ ಸಕ್ಕರೆ",
      "Same water and carbon dioxide • compare light": "ಅದೇ ನೀರು ಮತ್ತು ಕಾರ್ಬನ್ ಡೈಆಕ್ಸೈಡ್ • ಬೆಳಕನ್ನು ಹೋಲಿಸಿ",
      "Plant growth": "ಸಸ್ಯದ ಬೆಳವಣಿಗೆ",
      "Example data / trace": "ಉದಾಹರಣೆ ಡೇಟಾ / ಟ್ರೇಸ್",
      "Let's learn, one step at a time": "ಒಂದೊಂದೇ ಹಂತವಾಗಿ ಕಲಿಯೋಣ",
    };
    return dict[key] || key;
  }
  return key;
}

// Conservative local-font widths keep validated 120-character headings inside
// the SVG, including single words. Layout is a pure function of the text.
function textUnits(value: string): number {
  return Array.from(value).reduce((sum, character) => sum + (
    /[MWmw@%]/.test(character) ? 1 : /[A-Z]/.test(character) ? 0.8
      : /\s/.test(character) ? 0.35 : /[a-z0-9]/.test(character) ? 0.65 : 1
  ), 0);
}

function headingLines(value: string, width: number, size: number): string[] {
  const lines: string[] = [];
  let line = "";
  for (const word of value.split(/\s+/).filter(Boolean)) {
    if (line && textUnits(`${line} ${word}`) * size > width) {
      lines.push(line);
      line = "";
    }
    for (const character of `${line ? " " : ""}${word}`) {
      if (line && textUnits(line + character) * size > width) {
        lines.push(line.trim());
        line = "";
      }
      line += character;
    }
  }
  if (line.trim()) lines.push(line.trim());
  return lines;
}

function fitHeading(value: string, width: number, maximum: number, limit: number) {
  let size = maximum;
  let lines = headingLines(value, width, size);
  while (lines.length > limit && size > 18) {
    size -= 1;
    lines = headingLines(value, width, size);
  }
  return { lines, size };
}

export function GeneratedHeading({ heading }: { heading: string }) {
  const single = fitHeading(heading, 1110, 42, 1);
  const layout = single.size >= 34 ? single : fitHeading(heading, 1110, 34, 2);
  return <g>{layout.lines.map((line, index) =>
    <text key={index} x="85" y={layout.lines.length === 1 ? 152 : 130 + index * 35}
      fill="white" fontSize={layout.size} fontWeight="700">{line}</text>)}</g>;
}

function splitLines(value: string, max = 30, limit = 3): string[] {
  const lines: string[] = [];
  let current = "";
  for (const word of value.split(/\s+/)) {
    if (!word) continue;
    if (current && `${current} ${word}`.length > max) {
      lines.push(current);
      current = word;
    } else {
      current = current ? `${current} ${word}` : word;
    }
  }
  if (current) lines.push(current);
  return lines.slice(0, limit);
}

function Glyph({ label, x, y }: { label: string; x: number; y: number }) {
  const text = label.toLowerCase();
  return <g transform={`translate(${x} ${y})`} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    {/sun|light|solar/.test(text) ? <g stroke="#ffd16b" fill="#ffcf68">
      <circle r="25" />{Array.from({ length: 8 }, (_, i) => <line key={i}
        x1={Math.cos(i * Math.PI / 4) * 36} y1={Math.sin(i * Math.PI / 4) * 36}
        x2={Math.cos(i * Math.PI / 4) * 48} y2={Math.sin(i * Math.PI / 4) * 48} />)}
    </g> : /water|rain|absorb|root/.test(text) ? <g fill="#61c6f2" stroke="#a6e8ff">
      <path d="M 0 -43 C -12 -23 -33 -4 -30 17 C -26 51 29 50 31 17 C 33 -5 12 -23 0 -43 Z" />
      <path d="M -17 15 Q -16 28 -4 31" fill="none" />
    </g> : /carbon|co2|co₂|air/.test(text) ? <g stroke="#c2e4ff">
      <line x1="-32" y1="0" x2="32" y2="0" /><circle cx="-34" r="19" fill="#ee8a85" />
      <circle r="22" fill="#6687af" /><circle cx="34" r="19" fill="#ee8a85" />
      <text x="0" y="7" textAnchor="middle" fontSize="19" fill="white" stroke="none">C</text>
    </g> : /oxygen|o2|o₂/.test(text) ? <g stroke="#e1efff" fill="#ee8a85">
      <line x1="-19" y1="0" x2="19" y2="0" /><circle cx="-23" r="24" /><circle cx="23" r="24" />
    </g> : /sugar|glucose|energy|food|stor/.test(text) ? <g stroke="#ffdc85" fill="#866026">
      <path d="M 0 -38 L 33 -19 L 33 19 L 0 38 L -33 19 L -33 -19 Z" />
      <path d="M 6 -23 L -12 5 H 5 L -5 24 L 18 -7 H 1 Z" fill="#ffe6a0" stroke="none" />
    </g> : /leaf|plant|chlorophyll/.test(text) ? <g stroke="#a9ecac" fill="#3c9466">
      <path d="M -29 28 Q -48 -37 37 -38 Q 46 26 -29 28 Z" /><path d="M -34 37 L 21 -22" fill="none" />
    </g> : /print|i\s*=|iteration|value|loop|number/.test(text) ? <g stroke="#9dddee" fill="#173c5c">
      <rect x="-47" y="-34" width="94" height="68" rx="10" />
      <path d="M -31 -11 L -20 0 L -31 11 M -10 14 H 29" fill="none" />
      <text x="16" y="3" textAnchor="middle" fontSize="24" fill="#ffe19c" stroke="none">
        {label.match(/-?\d+/)?.[0] || ""}</text>
    </g> : <g stroke="#b2e7ed" fill="#285779">
      <circle cx="-25" cy="-17" r="17" /><circle cx="26" cy="-17" r="17" /><circle cy="27" r="17" />
      <path d="M -10 -17 H 10 M -17 0 L -7 13 M 17 0 L 7 13" fill="none" />
    </g>}
  </g>;
}

function Plant() {
  return <g strokeWidth="5" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="640" cy="494" rx="120" ry="15" fill="#73563b" opacity=".7" />
    <path d="M 640 480 V 297" stroke="#8ec89b" fill="none" />
    <path d="M 640 366 C 552 385 535 305 550 293 C 611 290 640 320 640 366 Z"
      fill="#3c9b68" stroke="#86d99e" />
    <path d="M 640 330 C 731 349 751 270 733 255 C 673 253 640 290 640 330 Z"
      fill="#4baa72" stroke="#a0e6ad" />
    <path d="M 640 365 L 567 312 M 640 330 L 714 276" stroke="#bee9b7" fill="none" />
    <path d="M 640 474 L 607 510 M 640 478 L 672 512 M 639 489 L 635 523"
      stroke="#d5ad74" fill="none" />
  </g>;
}

function LeafComparison({ scene, semanticScene, focus, progress, language }: {
  scene: Scene; semanticScene?: Scene; focus: number[]; progress: number; language?: string;
}) {
  const sem = semanticScene || scene;
  const semLabels = sem.items.map(labelOf);
  const labels = scene.items.map(labelOf);
  const lightIndex = semLabels.findIndex(item => /sunlit|sunlight|lit leaf|with light/i.test(item));
  const darkIndex = semLabels.findIndex(item => /dark|night|without light/i.test(item));
  return <g data-diagram="light-dark-prediction">
    {[{ x: 125, center: 365, dark: false, index: lightIndex },
      { x: 675, center: 915, dark: true, index: darkIndex }].map(panel =>
      <g key={panel.x}>
        <rect x={panel.x} y="210" width="480" height="330" rx="24"
          fill={panel.dark ? "#14243d" : "#183d50"}
          stroke={focus.includes(panel.index) ? "#ffcf68" : "#42647b"} strokeWidth="3" />
        <text x={panel.center} y="249" textAnchor="middle" fill="#e6f4ff" fontSize="27">
          {labels[panel.index] || (panel.dark ? tr("Without light", language) : tr("With light", language))}</text>
        <g transform={`translate(${panel.center - 640} 0)`}><Plant /></g>
        {panel.dark ? <g>
          <circle cx={panel.x + 405} cy="300" r="31" fill="#e8dcaa" />
          <circle cx={panel.x + 419} cy="289" r="29" fill="#14243d" />
        </g> : <Glyph label="Sunlight" x={panel.x + 73} y={300} />}
        <Glyph label="Sugar energy" x={panel.x + 405} y={450} />
        {panel.dark ? <path d={`M ${panel.x + 375} 420 l 60 60 m 0 -60 l -60 60`}
          stroke="#ed9695" strokeWidth="5" /> : <Flow
          points={[{ x: panel.center + 55, y: 360 }, { x: panel.x + 360, y: 440 }]}
          active={focus.includes(panel.index)} progress={progress} />}
        <text x={panel.x + 405} y={511} textAnchor="middle" fill="#f5dea1" fontSize="19">
          {panel.dark ? tr("No new sugar", language) : tr("New sugar", language)}</text>
      </g>)}
    <text x="640" y="566" textAnchor="middle" fill="#ffda8a" fontSize="23">
      {tr("Same water and carbon dioxide • compare light", language)}</text>
  </g>;
}

type Point = { x: number; y: number };
const labelOf = (item: string) => item.split(" :: ")[0].trim();

function flowPoint(points: Point[], progress: number): Point {
  const lengths = points.slice(1).map((p, i) => Math.hypot(p.x - points[i].x, p.y - points[i].y));
  let remaining = lengths.reduce((a, b) => a + b, 0) * Math.max(0, Math.min(1, progress));
  for (let i = 0; i < lengths.length; i += 1) {
    if (remaining <= lengths[i]) {
      const part = remaining / Math.max(.001, lengths[i]);
      return { x: points[i].x + (points[i + 1].x - points[i].x) * part,
        y: points[i].y + (points[i + 1].y - points[i].y) * part };
    }
    remaining -= lengths[i];
  }
  return points[points.length - 1];
}

function Flow({ points, active, progress, color = "#ffcf68" }: {
  points: Point[]; active: boolean; progress: number; color?: string;
}) {
  if (points.length < 2) return null;
  const dot = flowPoint(points, progress);
  return <g>
    <path d={points.map((p, i) => `${i ? "L" : "M"} ${p.x} ${p.y}`).join(" ")}
      fill="none" stroke={active ? color : "#6686a4"} opacity={active ? 1 : .45}
      strokeWidth={active ? 5 : 3} markerEnd="url(#generated-arrow)" />
    {active && <circle cx={dot.x} cy={dot.y} r="8" fill={color} stroke="white" strokeWidth="2" />}
  </g>;
}

function ArrowDefinition() {
  return <defs><marker id="generated-arrow" viewBox="0 0 10 10" refX="9" refY="5"
    markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#ffcf68" /></marker></defs>;
}

function CarbonGrowth({ scene, semanticScene, focus, progress, language }: {
  scene: Scene; semanticScene?: Scene; focus: number[]; progress: number; language?: string;
}) {
  const sem = semanticScene || scene;
  const semLabels = sem.items.map(labelOf);
  const labels = scene.items.map(labelOf);
  const carbon = Math.max(0, semLabels.findIndex(s => /carbon/i.test(s)));
  const sugar = Math.max(0, semLabels.findIndex(s => /sugar|energy|growth/i.test(s)));
  return <g data-diagram="carbon-to-growth">
    <ArrowDefinition />
    <circle cx="240" cy="350" r="76" fill="#173650" stroke="#6c9cb9" strokeWidth="3" />
    <Glyph label="Carbon dioxide" x={240} y={350} />
    <circle cx="640" cy="350" r="76" fill="#3c352c" stroke="#c5a260" strokeWidth="3" />
    <Glyph label="Sugar energy" x={640} y={350} />
    <g transform="translate(390 0)"><Plant /></g>
    <Flow points={[{ x: 325, y: 350 }, { x: 553, y: 350 }]} active={focus.includes(carbon)} progress={progress} />
    <Flow points={[{ x: 725, y: 350 }, { x: 952, y: 350 }]} active={focus.includes(sugar)} progress={progress} color="#91dfa7" />
    {[{ x: 240, text: labels[carbon] || semLabels[carbon] }, { x: 640, text: labels[sugar] || semLabels[sugar] }].map((node, i) => {
      const fit = fitHeading(node.text || "", 310, 27, 3);
      return <g key={i}>{fit.lines.map((line, j) => <text key={j} x={node.x} y={460 + j * 31}
        textAnchor="middle" fill="#e5effa" fontSize={fit.size}>{line}</text>)}</g>;
    })}
    <text x="1030" y="560" textAnchor="middle" fill="#a7e4b5" fontSize="26">
      {tr("Plant growth", language)}</text>
  </g>;
}

function ConceptDiagram({ scene, semanticScene, focus, progress }: {
  scene: Scene; semanticScene?: Scene; focus: number[]; progress: number;
}) {
  const sem = semanticScene || scene;
  const semNodes = sem.items.slice(0, 5).map(labelOf);
  const nodes = scene.items.slice(0, 5).map(labelOf);
  const plant = !semNodes.some(s => /dark|night|without|no light/i.test(s))
    && semNodes.filter(s => /sun|light|water|carbon|oxygen|glucose|chlorophyll|leaf/i.test(s)).length >= 2;
  return <g data-diagram={plant ? "plant-process" : "concept-process"}>
    <ArrowDefinition />
    {plant && <Plant />}
    {nodes.map((label, i) => {
      const semLabel = semNodes[i] || label;
      const role = /sun|light/i.test(semLabel) ? "sun" : /water|root/i.test(semLabel) ? "water"
        : /carbon|co2|co₂/i.test(semLabel) ? "carbon" : /oxygen|o2|o₂/i.test(semLabel) ? "oxygen" : "sugar";
      const slots: Record<string, Point> = { sun: { x: 200, y: 265 }, water: { x: 210, y: 455 },
        carbon: { x: 1040, y: 245 }, oxygen: { x: 1080, y: 375 }, sugar: { x: 1010, y: 470 } };
      const point = plant ? slots[role] : { x: 110 + (i + .5) * 1060 / nodes.length, y: 330 };
      const active = focus.includes(i);
      let path: Point[] = [];
      if (plant) {
        const targets: Record<string, Point> = { sun: { x: 576, y: 320 }, water: { x: 640, y: 480 },
          carbon: { x: 706, y: 300 }, oxygen: { x: 706, y: 300 }, sugar: { x: 676, y: 350 } };
        const target = targets[role], distance = Math.hypot(target.x - point.x, target.y - point.y);
        const edge = { x: point.x + (target.x - point.x) * 62 / distance,
          y: point.y + (target.y - point.y) * 62 / distance };
        path = role === "water" ? [edge, target, { x: 640, y: 370 }, { x: 614, y: 344 }]
          : role === "oxygen" || role === "sugar" ? [target, edge] : [edge, target];
      } else if (i < nodes.length - 1) {
        path = [{ x: point.x + 62, y: 330 }, { x: point.x + 1060 / nodes.length - 63, y: 330 }];
      }
      const side = plant && (role === "carbon" || role === "oxygen");
      const width = side ? 135 : plant ? 255 : Math.min(390, 1060 / nodes.length - 20);
      const fit = fitHeading(label, width, plant ? 23 : 24, side ? 3 : 2);
      return <g key={i} data-focus={active ? "active" : "rest"}>
        <Flow points={path} active={active} progress={progress} color={role === "water" ? "#68cfff" : "#ffcf68"} />
        <circle cx={point.x} cy={point.y} r="53" fill={active ? "#315369" : "#152d47"}
          stroke={active ? "#ffe09a" : "#355b78"} strokeWidth={active ? 5 : 1} />
        <Glyph label={semLabel} x={point.x} y={point.y} />
        {fit.lines.slice(0, side ? 3 : 2).map((line, j) => <text key={j}
          x={side ? point.x + 66 : point.x} y={side ? point.y - 9 + j * 24 : point.y + 80 + j * 24}
          textAnchor={side ? "start" : "middle"} fontSize={fit.size}
          fill={active ? "#ffe4aa" : "#e1edf8"}>{line}</text>)}
      </g>;
    })}
  </g>;
}

// Every changing highlight is selected by a measured speech cue, never a timer.
export default function DynamicSceneContent({ scene, semanticScene, cue, cueProgress = 0, language }: {
  scene: Scene; semanticScene?: Scene; progress: number; cue?: NarrationCue; cueProgress?: number; language?: string;
}) {
  if (scene.type === "title_card") {
    const heading = fitHeading(scene.heading, 1110, 51, 3);
    return <g>
      {heading.lines.map((line, i, all) => <text key={i} x="640"
        y={300 + (i - (all.length - 1) / 2) * 66} fill="#ffda76" textAnchor="middle"
        fontSize={heading.size} fontWeight="700">{line}</text>)}
      {splitLines(scene.subtitle || tr("Let's learn, one step at a time", language), 58, 2).map((line, i) =>
        <text key={i} x="640" y={425 + i * 42} fill="#dce5ff" textAnchor="middle" fontSize="27">{line}</text>)}
    </g>;
  }
  const focusedItems = cue?.item_indices || (cue?.item_index != null ? [cue.item_index] : []);
  const sem = semanticScene || scene;
  const content = sem.narration + " " + sem.items.map(labelOf).join(" ");
  const focusBadge = cue?.label && <text x="640" y="194" textAnchor="middle" fill="#ffda8a" fontSize="22">{cue.label}</text>;
  if (sem.type === "diagram" && /leaf/i.test(content) && /dark|night/i.test(content)
    && /lit leaf|with light|sunlit|sunlight/i.test(content)) {
    return <g>{cue?.label && <text x="640" y="194" textAnchor="middle" fill="#ffda8a" fontSize="22">{cue.label}</text>}
      <ArrowDefinition /><LeafComparison scene={scene} semanticScene={semanticScene} focus={focusedItems} progress={cueProgress} language={language} /></g>;
  }
  const labels = sem.items.map(labelOf).join(" ");
  if (sem.type === "step_list" && /carbon/i.test(labels) && /sugar|growth/i.test(labels)
    && !/recap|takeaway|check/i.test(sem.heading)) return <g>{focusBadge}<CarbonGrowth scene={scene} semanticScene={semanticScene} focus={focusedItems} progress={cueProgress} language={language} /></g>;
  if (sem.type === "diagram") return <g>{focusBadge}<ConceptDiagram scene={scene} semanticScene={semanticScene} focus={focusedItems} progress={cueProgress} /></g>;
  if (scene.type === "code_walkthrough") {
    const lines = (scene.code || "").split("\n").slice(0, 7);
    const active = cue?.highlight_lines.length ? cue.highlight_lines : scene.highlight_lines;
    const maxLength = Math.max(1, ...lines.map(line => line.length));
    const context = scene.items.map(labelOf).filter(item => !/^Line\s+\d/i.test(item) && !lines.some(line => line.trim() === item.trim())).slice(0, 5);
    const codeWidth = context.length ? 730 : 1100;
    const size = Math.min(31, (codeWidth - 155) / (maxLength * .62));
    return <g>
      <rect x="90" y="175" width={codeWidth} height="375" rx="22" fill="#0b1930" stroke="#5376a5" />
      {cue?.label && <text x={90 + codeWidth - 22} y="194" textAnchor="end" fill="#ffdc8a" fontSize="17">{cue.label}</text>}
      {lines.map((line, index) => <g key={index}>
        {active.includes(index + 1) && <rect x="110" y={201 + index * 48} width={codeWidth - 40} height="45" rx="9" fill="#275376" />}
        <text x="127" y={232 + index * 48} fill="#96b8e3" fontSize="19">{index + 1}</text>
        <text x="176" y={232 + index * 48} fill="#fff" fontSize={size}
          fontFamily="Consolas, monospace" xmlSpace="preserve">{line}</text>
      </g>)}
      {context.length > 0 && <g>
        <rect x="850" y="175" width="340" height="375" rx="22" fill="#19374c" stroke="#6b9cae" />
        <text x="875" y="212" fill="#ffda8a" fontSize="23">{tr("Example data / trace", language)}</text>
        {context.map((item, index) => {
          const layout = fitHeading(item, 285, 21, 2);
          const step = Math.min(110, 280 / context.length);
          return <g key={index}>{layout.lines.slice(0, 2).map((line, j) =>
            <text key={j} x="875" y={253 + index * step + j * 24}
              fill={focusedItems.includes(index) ? "#ffe2a0" : "#deedf8"}
              fontSize={layout.size}>{line}</text>)}</g>;
        })}
      </g>}
    </g>;
  }
  const items = scene.items.slice(0, 8).map(labelOf), step = Math.min(86, 345 / Math.max(1, items.length));
  return <g>{focusBadge}{items.map((item, i) => <g key={i} data-focus={focusedItems.includes(i) ? "active" : "rest"}>
    <circle cx="174" cy={219 + i * step} r="23" fill={focusedItems.includes(i) ? "#ffcc70" : "#658ba5"} />
    <text x="174" y={227 + i * step} textAnchor="middle" fontWeight="700" fill="#10223f" fontSize="24">{i + 1}</text>
    <text x="224" y={227 + i * step} fill="#f7f9ff" fontSize={items.length > 5 ? 23 : 28}>
      {item.length > 77 ? `${item.slice(0, 74)}…` : item}</text>
  </g>)}</g>;
}
