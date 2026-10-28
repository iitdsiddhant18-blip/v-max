"""Bounded trusted educational computations. Never eval/exec model code."""
import ast
import math
import re

LIMIT = 40


def check_spoken_outputs(code: str, narration: str) -> None:
    try:
        states=safe_trace(code)
    except ValueError:return  # Unsupported code gets explanation, never a claimed trace.
    actual=states[-1]['output'] if states else []
    numeric=[v for v in actual if re.fullmatch(r'-?\d+',v)]
    pattern=r'\b(?:prints?|outputs?|displays?)\s+(?:the\s+(?:values|numbers)\s+)?(-?\d+(?:(?:,\s*(?:and\s+)?|\s+and\s+)-?\d+)+)'
    for match in re.finditer(pattern,narration.lower()):
        if re.search(r'first|then|next|pass|iteration|initial',narration[max(0,match.start()-30):match.start()],re.I):continue
        stated=re.findall(r'-?\d+',match[1])
        if stated!=numeric:raise ValueError('Spoken output list contradicts the trusted bounded trace: '+', '.join(numeric))


def math_expression_from_text(text):
    """Extract an explicitly stated y/f(x) equation, not a model drawing expression."""
    text=text.lower().replace('²','**2').replace('³','**3').replace('^','**')
    text=re.sub(r'\bsquared\b','**2',text);text=re.sub(r'\bcubed\b','**3',text)
    for word,value in {'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10','plus':'+','minus':'-','times':'*'}.items():
        text=re.sub(r'\b'+word+r'\b',value,text)
    match=re.search(r'(?:\by\b|f\s*\(\s*x\s*\))\s*(?:=|equals)\s*',text)
    if not match:return None
    tail=text[match.end():];tokens=re.findall(r'\*\*|\d+(?:\.\d+)?|sin|cos|abs|exp|x|[()+*/-]|\S',tail)
    accepted=[]
    for token in tokens:
        if re.fullmatch(r'\d+(?:\.\d+)?|sin|cos|abs|exp|x|\*\*|[()+*/-]',token):accepted.append(token)
        else:break
    expression=''.join(accepted).rstrip('+-*/')
    expression=re.sub(r'(\d)(?=x|\()',r'\1*',expression)
    expression=re.sub(r'(?<=x)(?=\()|(?<=\))(?=x|\()', '*',expression)
    return expression if expression and len(expression)<=80 else None


def math_function_from_text(text):
    # A numeric substitution such as y=3² is a point, not the function rule.
    for match in re.finditer(r'(?:\by\b|f\s*\(\s*x\s*\))\s*(?:=|equals)',text,re.I):
        expression=math_expression_from_text(text[match.start():])
        if expression and re.search(r'\bx\b',expression):return expression
    if re.search(r'\bx\s*(?:squared|²)',text,re.I):return 'x**2'
    if re.search(r'\bx\s*(?:cubed|³)',text,re.I):return 'x**3'
    return None


def verified_function_parameters(expression):
    """Recover typed numeric parameters from a stated rule, with independent checks."""
    import numpy as np
    points=[-.875,-.375,.125,.625,1.125,1.625,2.125,2.625,3.125]
    def matches(data):
        for x in points:
            a,b=bounded_math_value(expression,x),function_value(data,x)
            if (a is None)!=(b is None) or (a is not None and abs(a-b)>1e-7*max(1,abs(a))):return False
        return True
    try:
        values=[bounded_math_value(expression,x) for x in (0,1,2,3,4)]
        if all(v is not None for v in values):
            coefficients=np.linalg.solve(np.array([[x**i for i in range(5)] for x in (0,1,2,3,4)],dtype=float),values)
            coefficients=[0.0 if abs(v)<1e-9 else float(round(v,10)) for v in coefficients]
            while len(coefficients)>1 and coefficients[-1]==0:coefficients.pop()
            data={'function':'polynomial','coefficients':coefficients,'scale':1,'frequency':1,'shift':0,'offset':0}
            if max(map(abs,coefficients))<=10000 and matches(data):return data
        for kind in ('reciprocal','absolute','exponential','sine','cosine'):
            data={'function':kind,'coefficients':[0,1],'scale':1,'frequency':1,'shift':0,'offset':0}
            if matches(data):return data
    except (ValueError,TypeError,OverflowError):return None
    return None


def bounded_math_value(expression,x):
    """Tiny AST-data interpreter for checking a stated equation. No eval/exec."""
    if not expression or len(expression)>80:raise ValueError('Math expression length limit')
    try:tree=ast.parse(expression,mode='eval')
    except SyntaxError as exc:raise ValueError('Unsupported mathematical notation') from exc
    if len(list(ast.walk(tree)))>40:raise ValueError('Math AST limit')
    def number(node,depth=0):
        if depth>8:raise ValueError('Math depth limit')
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):value=float(node.value)
        elif isinstance(node,ast.Name) and node.id=='x':value=x
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            value=number(node.operand,depth+1)*(-1 if isinstance(node.op,ast.USub) else 1)
        elif isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):
            a,b=number(node.left,depth+1),number(node.right,depth+1)
            if a is None or b is None:return None
            if isinstance(node.op,ast.Add):value=a+b
            elif isinstance(node.op,ast.Sub):value=a-b
            elif isinstance(node.op,ast.Mult):value=a*b
            elif isinstance(node.op,ast.Div):
                if abs(b)<1e-10:return None
                value=a/b
            else:
                if abs(b)>12:raise ValueError('Math exponent limit')
                try:value=a**b
                except (ValueError,OverflowError,ZeroDivisionError):return None
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('sin','cos','abs','exp') and len(node.args)==1 and not node.keywords:
            arg=number(node.args[0],depth+1)
            if arg is None:return None
            try:value={'sin':math.sin,'cos':math.cos,'abs':abs,'exp':math.exp}[node.func.id](arg)
            except (ValueError,OverflowError):return None
        else:raise ValueError('Unsupported math AST node')
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e6:return None
        return value
    return number(tree.body)


def hanoi(disks: int) -> list[dict]:
    if type(disks) is not int or not 2 <= disks <= 4:
        raise ValueError('Hanoi supports 2–4 disks')
    rods = {'a': list(range(disks, 0, -1)), 'b': [], 'c': []}
    result = [{'rods': {k: list(v) for k,v in rods.items()}, 'move': 0}]
    def move(n, source, target, spare):
        if not n:return
        move(n-1, source, spare, target)
        disk=rods[source].pop()
        if rods[target] and rods[target][-1]<disk:raise ValueError('Illegal Hanoi move')
        rods[target].append(disk)
        result.append({'rods':{k:list(v) for k,v in rods.items()},'move':len(result),
                       'source':source,'target':target,'disk':disk})
        move(n-1, spare, target, source)
    move(disks,'a','c','b')
    return result


def binary_search(values: list[int], target: int) -> list[dict]:
    if not 1 <= len(values) <= 12 or values != sorted(values) or len(set(values)) != len(values):
        raise ValueError('Binary search requires 1–12 distinct sorted values')
    if any(type(v) is not int or abs(v)>10000 for v in [*values,target]):raise ValueError('Invalid search value')
    low,high=0,len(values)-1; result=[]
    while low<=high:
        mid=(low+high)//2
        result.append({'low':low,'mid':mid,'high':high,'value':values[mid], 'found':values[mid]==target})
        if values[mid]==target:return result
        if values[mid]<target:low=mid+1
        else:high=mid-1
    result.append({'low':low,'high':high,'mid':None,'found':False})
    return result


def safe_trace(code: str) -> list[dict]:
    """Interpret a tiny AST data subset with no arbitrary calls or Python runtime execution."""
    if len(code)>1200 or len(code.splitlines())>12:raise ValueError('Trace code exceeds limits')
    try:tree=ast.parse(code)
    except SyntaxError as exc:raise ValueError('Invalid Python syntax') from exc
    if len(list(ast.walk(tree)))>150:raise ValueError('Trace AST exceeds limits')
    allowed=(ast.Module,ast.Assign,ast.AugAssign,ast.For,ast.If,ast.Expr,ast.Name,ast.Load,ast.Store,
             ast.Constant,ast.List,ast.Tuple,ast.BinOp,ast.UnaryOp,ast.Compare,ast.Call,
             ast.Add,ast.Sub,ast.Mult,ast.FloorDiv,ast.Mod,ast.USub,ast.UAdd,
             ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE)
    if any(not isinstance(n,allowed) for n in ast.walk(tree)):raise ValueError('Unsupported trace construct')
    env={}; output=[]; states=[]; work=0
    def bounded(value):
        if type(value) is int and abs(value)<=100000:return value
        if type(value) is bool:return value
        if type(value) is str and len(value)<=80:return value
        if isinstance(value,(list,tuple)) and len(value)<=12:return [bounded(v) for v in value]
        raise ValueError('Trace value exceeds limits')
    def expression(node,depth=0):
        nonlocal work
        work+=1
        if work>500 or depth>12:raise ValueError('Trace computation budget exceeded')
        if isinstance(node,ast.Constant):return bounded(node.value)
        if isinstance(node,ast.Name):
            if node.id not in env:raise ValueError('Undefined trace variable')
            return env[node.id]
        if isinstance(node,(ast.List,ast.Tuple)):return bounded([expression(n,depth+1) for n in node.elts])
        if isinstance(node,ast.UnaryOp):
            value=expression(node.operand,depth+1)
            if type(value) is not int:raise ValueError('Numeric operand required')
            return bounded(-value if isinstance(node.op,ast.USub) else value)
        if isinstance(node,ast.BinOp):
            a,b=expression(node.left,depth+1),expression(node.right,depth+1)
            if type(a) is not int or type(b) is not int:raise ValueError('Integer arithmetic only')
            if isinstance(node.op,ast.Add):value=a+b
            elif isinstance(node.op,ast.Sub):value=a-b
            elif isinstance(node.op,ast.Mult):value=a*b
            elif isinstance(node.op,ast.FloorDiv):
                if b==0:raise ValueError('Division by zero')
                value=a//b
            else:
                if b==0:raise ValueError('Division by zero')
                value=a%b
            return bounded(value)
        if isinstance(node,ast.Compare) and len(node.ops)==1:
            a,b=expression(node.left,depth+1),expression(node.comparators[0],depth+1)
            ops={ast.Eq:lambda:a==b,ast.NotEq:lambda:a!=b,ast.Lt:lambda:a<b,
                 ast.LtE:lambda:a<=b,ast.Gt:lambda:a>b,ast.GtE:lambda:a>=b}
            return ops[type(node.ops[0])]()
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='range' and not node.keywords:
            args=[expression(a,depth+1) for a in node.args]
            if not 1<=len(args)<=3 or any(type(v) is not int or abs(v)>10000 for v in args):raise ValueError('Bounded range required')
            try:values=range(*args)
            except ValueError as exc:raise ValueError('Invalid range') from exc
            if len(values)>12:raise ValueError('Range exceeds trace limit')
            return list(values)
        raise ValueError('Unsupported trace expression/call')
    def snapshot(node):
        if len(states)>=LIMIT:raise ValueError('Trace exceeds 40 steps')
        states.append({'line':node.lineno,'variables':{k:bounded(v) for k,v in env.items()},'output':list(output)})
    def block(nodes):
        for node in nodes:
            if isinstance(node,ast.Assign):
                if len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):raise ValueError('Simple assignment only')
                env[node.targets[0].id]=expression(node.value);snapshot(node)
            elif isinstance(node,ast.AugAssign):
                if not isinstance(node.target,ast.Name):raise ValueError('Simple assignment only')
                load=ast.Name(id=node.target.id,ctx=ast.Load())
                env[node.target.id]=expression(ast.BinOp(left=load,op=node.op,right=node.value));snapshot(node)
            elif isinstance(node,ast.For):
                if not isinstance(node.target,ast.Name) or node.orelse:raise ValueError('Simple loop only')
                values=expression(node.iter)
                if not isinstance(values,list) or len(values)>12:raise ValueError('Bounded list loop only')
                for value in values:
                    env[node.target.id]=value;snapshot(node);block(node.body)
            elif isinstance(node,ast.If):
                condition=expression(node.test);snapshot(node);block(node.body if condition else node.orelse)
            elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
                call=node.value
                if not isinstance(call.func,ast.Name) or call.func.id!='print' or call.keywords or len(call.args)>3:raise ValueError('Only print is permitted as a statement')
                output.append(' '.join(str(expression(arg)) for arg in call.args));snapshot(node)
            else:raise ValueError('Unsupported trace statement')
    block(tree.body)
    return states


def function_value(spec: dict, x: float) -> float | None:
    """Small typed numerical evaluator; there is no expression-string parser."""
    kind=spec['function']; c=spec.get('coefficients',[1,0]); shift=spec.get('shift',0)
    scale=spec.get('scale',1); u=(x-shift)*spec.get('frequency',1)
    try:
        if kind=='polynomial':value=sum(a*u**i for i,a in enumerate(c))
        elif kind=='absolute':value=abs(u)
        elif kind=='reciprocal':
            if abs(u)<1e-8:return None
            value=1/u
        elif kind=='exponential':value=math.exp(u)
        elif kind=='sine':value=math.sin(u)
        elif kind=='cosine':value=math.cos(u)
        else:raise ValueError('Unsupported typed function')
        value=value*scale+spec.get('offset',0)
        return value if math.isfinite(value) and abs(value)<=1e6 else None
    except (OverflowError,ZeroDivisionError):return None


def plot_samples(spec: dict, count=161) -> list[list[float] | None]:
    if not 2<=count<=241:raise ValueError('Plot sample cap exceeded')
    low,high=spec['x_min'],spec['x_max']; result=[]
    for i in range(count):
        x=low+(high-low)*i/(count-1); y=function_value(spec,x)
        # Never join across a pole; renderer also clips the numeric window.
        if spec['function']=='reciprocal' and i and (result[-1] is not None):
            previous=low+(high-low)*(i-1)/(count-1)
            if previous<=spec.get('shift',0)<=x:result.append(None)
        result.append(None if y is None else [x,y])
    return result
