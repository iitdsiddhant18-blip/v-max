"""Visual DSL v2: finite semantic DATA; geometry and time belong to trusted code."""
import math
import re
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ID=Annotated[str,Field(pattern=r'^[a-z][a-z0-9_]{0,39}$')]
Hash=Annotated[str,Field(pattern=r'^[0-9a-f]{64}$')]
Text=Annotated[str,Field(min_length=1,max_length=180)]
Number=Annotated[float,Field(ge=-10000,le=10000,allow_inf_nan=False)]
Positive=Annotated[float,Field(gt=0,le=10000,allow_inf_nan=False)]
Template=Literal['human_digestive_system','human_heart','plant_cell','animal_cell','leaf_photosynthesis']
ANCHORS={
 'human_digestive_system':('mouth','esophagus','stomach','pancreas','small_intestine','large_intestine','villi','bloodstream'),
 'human_heart':('right_atrium','right_ventricle','left_atrium','left_ventricle','lungs','body'),
 'plant_cell':('cell_wall','membrane','nucleus','cytoplasm','chloroplast','vacuole','mitochondrion'),
 'animal_cell':('membrane','nucleus','cytoplasm','mitochondrion'),
 'leaf_photosynthesis':('leaf','chloroplast','roots','stem','air','sugar','oxygen'),
}
ELEMENTS=set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())


def anchor_matches(anchor, label):
    name = anchor.replace('_', ' ')
    label = label.lower().replace('_', ' ')
    aliases = {
        'roots': ('root', 'roots', 'rhizoid'),
        'villi': ('villi', 'villus', 'microvilli'),
        'bloodstream': ('bloodstream', 'blood stream', 'blood vessel', 'capillary', 'capillaries', 'circulation', 'vessels', 'blood'),
        'small_intestine': ('small intestine', 'intestine', 'intestinal', 'ileum', 'jejunum', 'duodenum', 'gut', 'bowel', 'absorption'),
        'large_intestine': ('large intestine', 'colon', 'bowel', 'cecum', 'rectum'),
        'stomach': ('stomach', 'gastric', 'acid', 'pepsin', 'chyme'),
        'mouth': ('mouth', 'oral', 'teeth', 'saliva', 'tongue', 'chewing'),
        'esophagus': ('esophagus', 'gullet', 'swallowing', 'food pipe'),
        'pancreas': ('pancreas', 'pancreatic', 'insulin', 'enzymes'),
        'right_atrium': ('right atrium', 'atrium', 'atria', 'upper chamber', 'auricle', 'deoxygenated'),
        'left_atrium': ('left atrium', 'atrium', 'atria', 'upper chamber', 'auricle', 'pulmonary vein'),
        'right_ventricle': ('right ventricle', 'ventricle', 'lower chamber', 'pulmonary artery', 'pumping'),
        'left_ventricle': ('left ventricle', 'ventricle', 'lower chamber', 'aorta', 'pumping', 'apex'),
        'lungs': ('lungs', 'lung', 'pulmonary', 'alveoli', 'alveolus', 'gas exchange', 'oxygenation', 'respiratory'),
        'body': ('body', 'systemic', 'tissues', 'organs', 'systemic circulation'),
        'cell_wall': ('cell wall', 'wall', 'outer wall', 'cellulose', 'rigid boundary', 'protective layer', 'boundary'),
        'membrane': ('membrane', 'plasma membrane', 'cell membrane', 'bilayer', 'surface'),
        'nucleus': ('nucleus', 'nuclei', 'nuclear', 'dna', 'genetic', 'chromosomes', 'core'),
        'cytoplasm': ('cytoplasm', 'cytosol', 'fluid', 'matrix', 'internal fluid'),
        'chloroplast': ('chloroplast', 'chlorophyll', 'thylakoid', 'photosynthesis', 'green plastid'),
        'vacuole': ('vacuole', 'central vacuole', 'sap', 'tonoplast', 'storage'),
        'mitochondrion': ('mitochondrion', 'mitochondria', 'cristae', 'atp', 'powerhouse', 'energy'),
        'leaf': ('leaf', 'leaves', 'foliage', 'blade', 'mesophyll', 'stomata'),
        'stem': ('stem', 'stalk', 'shoot', 'vascular', 'xylem', 'phloem'),
        'air': ('air', 'atmosphere', 'co2', 'carbon dioxide', 'gas', 'ambient'),
        'sugar': ('sugar', 'glucose', 'sucrose', 'sap', 'carbohydrate', 'product'),
        'oxygen': ('oxygen', 'o2', 'gas product'),
    }
    return any(alias in label for alias in aliases.get(anchor, (name,)))


class Frozen(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,allow_inf_nan=False)


class Entity(Frozen):
    id: ID
    role: Literal['part','input','output','process','quantity','state','event','object','context']
    label_key: ID
    anchor_id: ID | None=None


class Relationship(Frozen):
    source: ID
    target: ID
    kind: Literal['flow','causes','sequence','contains','exchange','comparison']
    label_key: ID


class BeatAction(Frozen):
    beat_index: int=Field(ge=0,le=7)
    op: Literal['reveal','highlight','connect','trace_path','move_entity','pulse','zoom_region',
                'plot_to_x','secant_to_tangent','set_state','pour','emphasize_term']
    target_ids: tuple[ID,...]=Field(min_length=1,max_length=4)
    state_index: int | None=Field(default=None,ge=0,le=40)
    value: Number | None=None


class MapData(Frozen):
    kind: Literal['concept_map','flow_process','generic_diagram']
    layout: Literal['row','tree','cycle']='row'


class IllustrationData(Frozen):
    kind: Literal['labelled_illustration']='labelled_illustration'
    zoom: Literal['none','focused_part']='focused_part'


class PlotData(Frozen):
    kind: Literal['function_plot']='function_plot'
    function: Literal['polynomial','reciprocal','absolute','exponential','sine','cosine']
    coefficients: tuple[Number,...]=Field(default=(0,1),min_length=1,max_length=5)
    scale: Number=1
    frequency: Positive=1
    shift: Number=0
    offset: Number=0
    x_min: Number=-4
    x_max: Number=4
    y_min: Number=-2
    y_max: Number=10
    x_label_key: ID
    y_label_key: ID
    curve_label_key: ID
    point_xs: tuple[Number,...]=Field(default=(),max_length=6)
    tangent_x: Number | None=None
    secant_x: Number | None=None
    shade_interval: tuple[Number,Number] | None=None

    @model_validator(mode='after')
    def window(self):
        if self.x_max-self.x_min<.01 or self.y_max-self.y_min<.01:raise ValueError('Nonzero increasing plot window required')
        if max(abs(self.x_min),abs(self.x_max))>100 or self.x_max-self.x_min>100:raise ValueError('Plot x window exceeds safe limits')
        if any(not self.x_min<=x<=self.x_max for x in self.point_xs):raise ValueError('Point outside x window')
        if self.shade_interval and not self.x_min<=self.shade_interval[0]<self.shade_interval[1]<=self.x_max:raise ValueError('Invalid shaded interval')
        from .algorithm_trace import function_value
        for x in (*self.point_xs,*([self.tangent_x] if self.tangent_x is not None else [])):
            if not self.x_min<=x<=self.x_max or function_value(self.model_dump(),x) is None:raise ValueError('Undefined marked point/tangent')
        return self


class Interval(Frozen):
    start: Number
    end: Number
    start_closed: bool=True
    end_closed: bool=True
    @model_validator(mode='after')
    def order(self):
        if self.start>=self.end:raise ValueError('Interval must increase')
        return self


class NumberLineData(Frozen):
    kind: Literal['number_line']='number_line'
    minimum: Number=-3
    maximum: Number=3
    points: tuple[Number,...]=Field(min_length=1,max_length=8)
    intervals: tuple[Interval,...]=Field(default=(),max_length=3)
    axis_label_key: ID
    @model_validator(mode='after')
    def extent(self):
        if self.maximum-self.minimum<.01:raise ValueError('Number line needs an increasing range')
        if any(not self.minimum<=p<=self.maximum for p in self.points):raise ValueError('Number-line point outside range')
        if any(i.start<self.minimum or i.end>self.maximum for i in self.intervals):raise ValueError('Interval outside number line')
        return self


class ChartSeries(Frozen):
    label_key: ID
    values: tuple[Number,...]=Field(min_length=1,max_length=8)


class ChartData(Frozen):
    kind: Literal['data_chart']='data_chart'
    chart: Literal['bar','line','pie']='bar'
    category_keys: tuple[ID,...]=Field(min_length=1,max_length=8)
    series: tuple[ChartSeries,...]=Field(min_length=1,max_length=3)
    x_label_key: ID
    y_label_key: ID
    @model_validator(mode='after')
    def values(self):
        if any(len(s.values)!=len(self.category_keys) for s in self.series):raise ValueError('Chart length mismatch')
        if self.chart in ('bar','pie') and any(v<0 for s in self.series for v in s.values):raise ValueError('Bar/pie requires nonnegative values with zero baseline')
        if self.chart=='pie' and (len(self.series)!=1 or sum(self.series[0].values)<=0):raise ValueError('Pie needs one positive-total series')
        return self


class Vector(Frozen):
    entity_id: ID
    x: Number
    y: Number
    unit: Literal['N','m/s','m','m/s²']


class ForceData(Frozen):
    kind: Literal['force_motion']='force_motion'
    mode: Literal['force','motion','circuit','wave']='force'
    mass_kg: Positive=1
    vectors: tuple[Vector,...]=Field(default=(),max_length=6)
    displacement_m: Number=5
    seconds: Positive=2
    resistance_ohm: Positive=2
    voltage_v: Positive=6
    amplitude: Positive=1
    frequency_hz: Positive=1
    schematic_label_key: ID
    @model_validator(mode='after')
    def limits(self):
        if self.mode=='wave' and self.frequency_hz>6:raise ValueError('Schematic wave frequency exceeds visible sample budget')
        if self.mode=='force' and any(v.unit!='N' for v in self.vectors):raise ValueError('Force vectors require newtons')
        if self.mode=='force' and not self.vectors:raise ValueError('Force demonstration needs named force vectors')
        return self


class FormulaData(Frozen):
    kind: Literal['formula','equation_balance']
    expression_key: ID
    step_keys: tuple[ID,...]=Field(min_length=1,max_length=6)
    # When supplied, trusted code derives every ax+b=c solution step.
    linear_equation: tuple[Number,Number,Number] | None=None
    @model_validator(mode='after')
    def solvable(self):
        if self.linear_equation and self.linear_equation[0]==0:raise ValueError('Equation coefficient must be nonzero')
        if self.linear_equation and len(self.step_keys)!=3:raise ValueError('Typed linear solution has exactly three verified steps')
        return self


class Species(Frozen):
    formula: Annotated[str,Field(pattern=r'^(?:[A-Z][a-z]?[0-9]{0,2}){1,8}$',max_length=40)]
    coefficient: int=Field(ge=1,le=20)
    label_key: ID
    state: Literal['s','l','g','aq','unspecified']='unspecified'


class ReactionData(Frozen):
    kind: Literal['reaction_equation']='reaction_equation'
    reactants: tuple[Species,...]=Field(min_length=1,max_length=4)
    products: tuple[Species,...]=Field(min_length=1,max_length=4)
    @model_validator(mode='after')
    def conserved(self):
        def atoms(species):
            result={}
            for s in species:
                for atom,count in re.findall(r'([A-Z][a-z]?)([0-9]*)',s.formula):
                    if atom not in ELEMENTS:raise ValueError('Unknown elemental symbol')
                    n=int(count or 1)
                    if n==0:raise ValueError('Zero atom subscript')
                    result[atom]=result.get(atom,0)+n*s.coefficient
            return result
        if atoms(self.reactants)!=atoms(self.products):raise ValueError('Unbalanced reaction: atom conservation failed')
        return self


class Apparatus(Frozen):
    entity_id: ID
    shape: Literal['beaker','test_tube','flask','cylinder','pipette','funnel']
    volume_ml: Annotated[float,Field(ge=0,le=1000,allow_inf_nan=False)]
    capacity_ml: Positive
    solute_units: Annotated[float,Field(ge=0,le=1000,allow_inf_nan=False)]=0
    @model_validator(mode='after')
    def capacity(self):
        if self.volume_ml>self.capacity_ml:raise ValueError('Apparatus overflow')
        return self


class LabData(Frozen):
    kind: Literal['lab_process']='lab_process'
    apparatus: tuple[Apparatus,...]=Field(min_length=2,max_length=4)
    source_id: ID
    target_id: ID
    transfer_ml: Positive
    illustration_label_key: ID
    @model_validator(mode='after')
    def transfer(self):
        by_id={a.entity_id:a for a in self.apparatus}
        if len(by_id)!=len(self.apparatus) or self.source_id==self.target_id or not {self.source_id,self.target_id}<=by_id.keys():raise ValueError('Invalid apparatus transfer')
        source,target=by_id[self.source_id],by_id[self.target_id]
        if self.transfer_ml>source.volume_ml or target.volume_ml+self.transfer_ml>target.capacity_ml:raise ValueError('Nonconserving volume/overflow')
        return self


class CodeData(Frozen):
    kind: Literal['code_trace']='code_trace'
    code: Annotated[str,Field(min_length=1,max_length=1200)]
    trace_mode: Literal['bounded','explanation']='bounded'
    variables_label_key: ID
    output_label_key: ID
    status_label_key: ID


class AlgorithmData(Frozen):
    kind: Literal['algorithm_state']='algorithm_state'
    algorithm: Literal['hanoi','binary_search']
    disks: int=Field(default=3,ge=2,le=4)
    values: tuple[int,...]=Field(default=(1,3,5,7,9),min_length=1,max_length=12)
    target: int=Field(default=7,ge=-10000,le=10000)
    state_label_key: ID
    pointer_keys: tuple[ID,...]=Field(min_length=3,max_length=3)
    @model_validator(mode='after')
    def valid(self):
        if self.algorithm=='binary_search':
            from .algorithm_trace import binary_search
            binary_search(list(self.values),self.target)
        return self


class TimelineEvent(Frozen):
    entity_id: ID
    time_label_key: ID
    order: int=Field(ge=0,le=12)


class TimelineData(Frozen):
    kind: Literal['timeline']='timeline'
    events: tuple[TimelineEvent,...]=Field(min_length=2,max_length=8)
    @model_validator(mode='after')
    def order(self):
        values=[e.order for e in self.events]
        if values!=sorted(set(values)):raise ValueError('Timeline must have unique ordered events')
        return self


class ComparisonData(Frozen):
    kind: Literal['comparison','table']
    column_keys: tuple[ID,...]=Field(min_length=2,max_length=3)
    rows: tuple[tuple[ID,...],...]=Field(min_length=1,max_length=5)
    @model_validator(mode='after')
    def columns(self):
        if any(len(r)!=len(self.column_keys) for r in self.rows):raise ValueError('Comparison column mismatch')
        return self


Data=Annotated[Union[MapData,IllustrationData,PlotData,NumberLineData,ChartData,ForceData,
                     FormulaData,ReactionData,LabData,CodeData,AlgorithmData,TimelineData,ComparisonData],Field(discriminator='kind')]
Family=Literal['concept_map','flow_process','generic_diagram','labelled_illustration','function_plot',
               'number_line','data_chart','force_motion','formula','equation_balance',
               'reaction_equation','lab_process','code_trace','algorithm_state','timeline','comparison','table']


class VisualScene(Frozen):
    scene_index: int=Field(ge=0,le=5)
    family: Family
    template_id: Template | None=None
    entities: tuple[Entity,...]=Field(min_length=1,max_length=12)
    relationships: tuple[Relationship,...]=Field(default=(),max_length=16)
    display_text_en: dict[ID,Text]=Field(min_length=1,max_length=64)
    beat_actions: tuple[BeatAction,...]=Field(min_length=1,max_length=32)
    data: Data

    @model_validator(mode='after')
    def references(self):
        if self.family!=self.data.kind:raise ValueError('Family/payload mismatch')
        ids=[e.id for e in self.entities]; labels=set(self.display_text_en)
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate entity IDs')
        for text in self.display_text_en.values():
            if re.search(r'<|>|https?://|javascript:|data:|[\x00-\x08]',text,re.I):raise ValueError('Unsafe display text')
        if any(e.label_key not in labels for e in self.entities):raise ValueError('Missing entity display text key')
        if self.family=='labelled_illustration':
            if self.template_id is None:raise ValueError('Illustration requires known template')
            if any(e.anchor_id is not None and e.anchor_id not in ANCHORS[self.template_id] for e in self.entities):raise ValueError('Unknown illustration anchor')
            if not any(e.anchor_id is not None for e in self.entities):raise ValueError('Illustration needs at least one actual installed part anchor')
            for entity in self.entities:
                if entity.anchor_id is None:
                    if entity.role=='part':raise ValueError('A named part needs a supported anchor; use a context node otherwise')
                    continue
                # A whole stomach anchor cannot silently become a precise
                # sphincter, nor an intestine anchor an unsupported organ.
                if not anchor_matches(entity.anchor_id,self.display_text_en[entity.label_key]):
                    raise ValueError('Illustration label must name its actual supported anchor: '+entity.anchor_id.replace('_',' '))
        elif self.template_id is not None or any(e.anchor_id is not None for e in self.entities):raise ValueError('Anchors only supported in labelled illustrations')
        for r in self.relationships:
            if r.source not in ids or r.target not in ids or r.source==r.target:raise ValueError('Dangling/self relationship')
            if r.label_key not in labels:raise ValueError('Missing relationship label')
        allowed={'reveal','highlight','pulse'}
        if self.family in ('concept_map','flow_process','generic_diagram','labelled_illustration'):allowed|={'connect','trace_path','zoom_region'}
        if self.family=='function_plot':allowed|={'plot_to_x','trace_path','secant_to_tangent'}
        if self.family in ('number_line','force_motion'):allowed|={'move_entity','trace_path'}
        if self.family in ('algorithm_state','code_trace'):allowed|={'set_state'}
        if self.family=='lab_process':allowed|={'pour'}
        if self.family in ('formula','equation_balance','reaction_equation'):allowed|={'emphasize_term'}
        for a in self.beat_actions:
            if not set(a.target_ids)<=set(ids):raise ValueError('Action target missing')
            if a.op not in allowed:raise ValueError('Action incompatible with visual family')
            if a.op=='set_state' and a.state_index is None:raise ValueError('set_state needs state_index')
            if a.op=='plot_to_x' and (a.value is None or not self.data.x_min<=a.value<=self.data.x_max):raise ValueError('plot_to_x needs an in-window x')
            if a.op=='secant_to_tangent' and (self.data.tangent_x is None or self.data.secant_x is None):raise ValueError('Tangent transition needs two specified x values')
            if a.op in ('connect','trace_path') and len(a.target_ids)==2:
                if not any(r.source==a.target_ids[0] and r.target==a.target_ids[1] for r in self.relationships):raise ValueError('Action references absent relationship')
        # Recursively validate every typed key/ref; payload cannot hide extra text.
        def keys(value,key=''):
            if isinstance(value,dict):
                for k,v in value.items():keys(v,k)
            elif isinstance(value,(list,tuple)):
                for v in value:keys(v,key)
            elif isinstance(value,str):
                if key.endswith('_key') or key in ('category_keys','column_keys','rows','step_keys','pointer_keys'):
                    if value not in labels:raise ValueError('Unrecognized payload text key: '+value)
                if key in ('entity_id','source_id','target_id') and value not in ids:raise ValueError('Payload entity reference missing')
        keys(self.data.model_dump())
        if isinstance(self.data,MapData) and self.data.layout=='tree':
            graph={i:[] for i in ids}
            for r in self.relationships:graph[r.source].append(r.target)
            def visit(node,path):
                if node in path:raise ValueError('Cycle prohibited in tree layout')
                for target in graph[node]:visit(target,path|{node})
            for node in ids:visit(node,set())
        return self


class VisualPlan(Frozen):
    visual_schema_version: Literal[2]=2
    source_lesson_id: Hash
    scenes: tuple[VisualScene,...]=Field(min_length=3,max_length=6)
    @model_validator(mode='after')
    def ordered(self):
        if [s.scene_index for s in self.scenes]!=list(range(len(self.scenes))):raise ValueError('Visual scene order must be complete and stable')
        return self
