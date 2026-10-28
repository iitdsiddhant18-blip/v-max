import type {VisualProps} from "./contracts";
import {ConceptMap,Comparison,Timeline,Algorithm,CodeTrace} from "./StructuralScenes";
import {FunctionPlot,NumberLine,Chart,Formula,ForceMotion,Reaction,LabProcess} from "./NumericScenes";
import Illustrations from "./Illustrations";
import {activeIds} from "./animation";
export default function VisualDispatcher(props:VisualProps){
 const {spec,beat,progress}=props;
 const families={concept_map:ConceptMap,flow_process:ConceptMap,generic_diagram:ConceptMap,
  labelled_illustration:Illustrations,function_plot:FunctionPlot,number_line:NumberLine,data_chart:Chart,
  force_motion:ForceMotion,formula:Formula,equation_balance:Formula,reaction_equation:Reaction,
  lab_process:LabProcess,code_trace:CodeTrace,algorithm_state:Algorithm,timeline:Timeline,
  comparison:Comparison,table:Comparison};
 const Component=families[spec.family];
 return <g data-visual-family={spec.family} data-beat={beat} data-cue-progress={progress.toFixed(6)}
  data-active-ids={Array.from(activeIds(spec,beat)).sort().join(",")}>
  <Component {...props}/>
 </g>;
}
