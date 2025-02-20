import ast,sys,os,unittest
from io import StringIO
from textwrap import dedent
from python_minifier import minify

class SelfToSeTransformer(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  for a in n.args.args:
   if a.arg=='se':a.arg='self'
  self.generic_visit(n)
  return n
 def visit_Attribute(self,n):
  if isinstance(n.value,ast.Name)and n.value.id=='se':
   n.value.id='self'
  self.generic_visit(n)
  return n

def transform_code(c):
 t=SelfToSeTransformer().visit(ast.parse(c))
 ast.fix_missing_locations(t)
 return unparse(t)

def unparse(n,i=0):
 s=' '*i
 if isinstance(n,ast.Module):return'\n'.join(unparse(x)for x in n.body)
 if isinstance(n,ast.ClassDef):return f"{s}class {n.name}:\n"+'\n'.join(unparse(x,i+4)for x in n.body)
 if isinstance(n,ast.FunctionDef):return f"{s}def {n.name}({','.join(a.arg for a in n.args.args)}):\n"+'\n'.join(unparse(x,i+4)for x in n.body)
 if isinstance(n,ast.Assign):return f"{s}{' = '.join(unparse(t)for t in n.targets)} = {unparse(n.value)}"
 if isinstance(n,ast.Name):return n.id
 if isinstance(n,ast.Constant):return repr(n.value)
 if isinstance(n,ast.Call):return f"{s}{unparse(n.func)}({','.join(unparse(a)for a in n.args)})"if i else f"{unparse(n.func)}({','.join(unparse(a)for a in n.args)})"
 if isinstance(n,ast.Attribute):return f"{unparse(n.value)}.{n.attr}"
 if isinstance(n,ast.Expr):return f"{s}{unparse(n.value)}"
 return''

class CodeTransformer:
 def __init__(self):
  self.o,self.s=sys.stdout,StringIO()
 def transform_and_execute(self,c):
  m=minify(transform_code(c))
  sys.stdout=self.s
  exec(m,globals())
  sys.stdout=self.o
  o=self.s.getvalue().strip()
  self.s.truncate(0)
  self.s.seek(0)
  return o
 @staticmethod
 def get_project_size(f):
  return os.path.getsize(f)

def main(f=None):
 t=CodeTransformer()
 if not f:
  c="class Test:\n def __init__(se):\n  se.value=42\n def print_value(se):\n  print(se.value)\nobj=Test()\nobj.print_value()"
  print('Output:',t.transform_and_execute(c))
  open("t.py","w").write(minify(transform_code(c)))
  print(f"Size: {t.get_project_size('t.py')} bytes")
  os.remove("t.py")
 else:
  with open(f,'r',encoding='utf-8')as r:c=r.read()
  print('Output:',t.transform_and_execute(c))
  print(f"Size: {t.get_project_size(f)} bytes")

class TestSelfTransformer(unittest.TestCase):
 def test_transform_code(self):
  c="class Test:\n def __init__(se):\n  se.value=10"
  e="class Test:\n    def __init__(self):\n        self.value = 10"
  self.assertEqual(transform_code(c),e)
 def test_execute(self):
  c="class Test:\n def __init__(se):\n  se.value=42\n def print_value(se):\n  print(se.value)\nobj=Test()\nobj.print_value()"
  self.assertEqual(CodeTransformer().transform_and_execute(c),"42")

if __name__=="__main__":
 unittest.main(argv=[''],exit=False)
 main(sys.argv[1]if len(sys.argv)>1 else None)
