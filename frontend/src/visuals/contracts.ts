// Generated from backend/app/visual_schema.py JSON schema. Canonical serialized values include defaults.

export type AlgorithmData = {
  kind: "algorithm_state";
  algorithm: "hanoi" | "binary_search";
  disks: number;
  values: (number)[];
  target: number;
  state_label_key: string;
  pointer_keys: (string)[];
};

export type Apparatus = {
  entity_id: string;
  shape: "beaker" | "test_tube" | "flask" | "cylinder" | "pipette" | "funnel";
  volume_ml: number;
  capacity_ml: number;
  solute_units: number;
};

export type BeatAction = {
  beat_index: number;
  op: "reveal" | "highlight" | "connect" | "trace_path" | "move_entity" | "pulse" | "zoom_region" | "plot_to_x" | "secant_to_tangent" | "set_state" | "pour" | "emphasize_term";
  target_ids: (string)[];
  state_index: number | null;
  value: number | null;
};

export type ChartData = {
  kind: "data_chart";
  chart: "bar" | "line" | "pie";
  category_keys: (string)[];
  series: (ChartSeries)[];
  x_label_key: string;
  y_label_key: string;
};

export type ChartSeries = {
  label_key: string;
  values: (number)[];
};

export type CodeData = {
  kind: "code_trace";
  code: string;
  trace_mode: "bounded" | "explanation";
  variables_label_key: string;
  output_label_key: string;
  status_label_key: string;
};

export type ComparisonData = {
  kind: "comparison" | "table";
  column_keys: (string)[];
  rows: ((string)[])[];
};

export type Entity = {
  id: string;
  role: "part" | "input" | "output" | "process" | "quantity" | "state" | "event" | "object" | "context";
  label_key: string;
  anchor_id: string | null;
};

export type ForceData = {
  kind: "force_motion";
  mode: "force" | "motion" | "circuit" | "wave";
  mass_kg: number;
  vectors: (Vector)[];
  displacement_m: number;
  seconds: number;
  resistance_ohm: number;
  voltage_v: number;
  amplitude: number;
  frequency_hz: number;
  schematic_label_key: string;
};

export type FormulaData = {
  kind: "formula" | "equation_balance";
  expression_key: string;
  step_keys: (string)[];
  linear_equation: [number, number, number] | null;
};

export type IllustrationData = {
  kind: "labelled_illustration";
  zoom: "none" | "focused_part";
};

export type Interval = {
  start: number;
  end: number;
  start_closed: boolean;
  end_closed: boolean;
};

export type LabData = {
  kind: "lab_process";
  apparatus: (Apparatus)[];
  source_id: string;
  target_id: string;
  transfer_ml: number;
  illustration_label_key: string;
};

export type MapData = {
  kind: "concept_map" | "flow_process" | "generic_diagram";
  layout: "row" | "tree" | "cycle";
};

export type NumberLineData = {
  kind: "number_line";
  minimum: number;
  maximum: number;
  points: (number)[];
  intervals: (Interval)[];
  axis_label_key: string;
};

export type PlotData = {
  kind: "function_plot";
  function: "polynomial" | "reciprocal" | "absolute" | "exponential" | "sine" | "cosine";
  coefficients: (number)[];
  scale: number;
  frequency: number;
  shift: number;
  offset: number;
  x_min: number;
  x_max: number;
  y_min: number;
  y_max: number;
  x_label_key: string;
  y_label_key: string;
  curve_label_key: string;
  point_xs: (number)[];
  tangent_x: number | null;
  secant_x: number | null;
  shade_interval: [number, number] | null;
};

export type ReactionData = {
  kind: "reaction_equation";
  reactants: (Species)[];
  products: (Species)[];
};

export type Relationship = {
  source: string;
  target: string;
  kind: "flow" | "causes" | "sequence" | "contains" | "exchange" | "comparison";
  label_key: string;
};

export type Species = {
  formula: string;
  coefficient: number;
  label_key: string;
  state: "s" | "l" | "g" | "aq" | "unspecified";
};

export type TimelineData = {
  kind: "timeline";
  events: (TimelineEvent)[];
};

export type TimelineEvent = {
  entity_id: string;
  time_label_key: string;
  order: number;
};

export type Vector = {
  entity_id: string;
  x: number;
  y: number;
  unit: "N" | "m/s" | "m" | "m/s\u00b2";
};

export type VisualScene = {
  scene_index: number;
  family: "concept_map" | "flow_process" | "generic_diagram" | "labelled_illustration" | "function_plot" | "number_line" | "data_chart" | "force_motion" | "formula" | "equation_balance" | "reaction_equation" | "lab_process" | "code_trace" | "algorithm_state" | "timeline" | "comparison" | "table";
  template_id: "human_digestive_system" | "human_heart" | "plant_cell" | "animal_cell" | "leaf_photosynthesis" | null;
  entities: (Entity)[];
  relationships: (Relationship)[];
  display_text_en: Record<string, unknown>;
  beat_actions: (BeatAction)[];
  data: MapData | IllustrationData | PlotData | NumberLineData | ChartData | ForceData | FormulaData | ReactionData | LabData | CodeData | AlgorithmData | TimelineData | ComparisonData;
};

export type VisualPlan = {
  visual_schema_version: 2;
  source_lesson_id: string;
  scenes: (VisualScene)[];
};

export interface TraceState { line?: number; variables?: Record<string, unknown>; output?: string[]; rods?: Record<string, number[]>; move?: number; source?: string; target?: string; disk?: number; low?: number; mid?: number | null; high?: number; found?: boolean; value?: number; }
export interface Computed { explanation_lines?: number[]; samples?: ([number,number] | null)[]; points?: [number,number][]; tangent?: {x:number;y:number;slope:number}; secant?: {x:number;y:number;slope:number}; secant_path?: {x:number;y:number;slope:number}[]; states?: TraceState[]; equation_steps?: string[]; net_force?: number[]; acceleration?: number[]; }
export interface VisualProps { spec: VisualScene; labels: Record<string,string>; computed: Computed; beat: number; progress: number; }
