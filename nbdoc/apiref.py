# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/apiref.ipynb (unless otherwise specified).

__all__ = ['Parsed', 'ParsedFunc', 'ParsedClass', 'ParsedModule']

# Cell
from fastcore.all import Path, L, risinstance, test_eq
import ast, re

# Cell
class Parsed:
    "Base class for Parsed objects used to store structured data about an AST."
    def __init__(self, tree):
        self.tree = tree
        self.docstring = ast.get_docstring(tree)

    def __getattr__(self, a):
        return getattr(self.tree, a)

# Cell
class ParsedFunc(Parsed):
    "Parse a function in a way that is amenable to show in the docs."
    def __init__(self, tree):
        assert isinstance(tree, ast.FunctionDef), f"Cannot parse non-function type: {type(tree)}."
        super().__init__(tree)
        self.dirty_ds = ast.get_docstring(tree, clean=False)
        self.args = ast.unparse(tree.args)
        _returns = getattr(tree, 'returns')
        self.returns = ast.unparse(_returns) if _returns else None
        self.body = self.get_body()
        self.decorators = [ast.unparse(d) for d in tree.decorator_list]

    def get_body(self):
        body = ast.unparse(self.tree.body).encode('utf-8').decode('unicode_escape')
        docstring = f"'{ast.get_docstring(self.tree, clean=False)}'\n"
        return body.replace(docstring, '')

    @property
    def include(self):
        "If this function should be shown in the docs or not."
        return self.name == '__init__' or (not self.name.startswith('_') and 'property' not in self.decorators)

# Cell
class ParsedClass(Parsed):
    "Parse Python Classes and associated methods."
    def __init__(self, tree):
        assert isinstance(tree, ast.ClassDef), f"Cannot parse non-class type: {type(tree)}."
        super().__init__(tree)
        self.docstring = ast.get_docstring(tree)
        self._methods = self.get_funcs()
        self.methods = []
        for m in self._methods:
            if m.name != '__init__':
                self.methods.append(m)
            elif m.name == '__init__':
                self._init_method = m
                self.signature = m.args

    @property
    def include(self):
        return not self.name.startswith('_') and bool(self._methods)


    def get_funcs(self):
        _funcs = L(self.tree.body).filter(risinstance(ast.FunctionDef)).map(lambda x: ParsedFunc(x))
        return _funcs.filter(lambda x: x.include)

# Cell
class ParsedModule(Parsed):
    "Parse python modules given a `basedir` and `filepath`"
    def __init__(self, basedir:str, filepath:str):
        fp = Path(filepath)
        bd = Path(basedir)
        assert filepath.startswith(basedir), f"`filepath`: {filepath} must start with `basedir`: {basedir}"
        assert fp.exists(), f'File does not exist: {str(fp)}'
        assert fp.suffix == '.py', f'Only python files can be parsed.  Got: f{str(fp)}'


        tree = ast.parse(fp.read_text())
        super().__init__(tree)

        self.stem = fp.stem
        self.source_dir = re.sub(r'^/', '', str(fp.parent).replace(str(bd), ''))
        self.dest_dir = f"{self.source_dir}/{self.stem}"

        assert isinstance(tree, ast.Module), f"Cannot parse non-Module type: {type(tree)}."
        self.funcs = L()
        self.classes = L()
        for o in L(tree.body).filter(risinstance((ast.FunctionDef, ast.ClassDef))):
            if isinstance(o, ast.FunctionDef):
                f = ParsedFunc(o)
                if f.include: self.funcs.append(f)
            if isinstance(o, ast.ClassDef):
                c = ParsedClass(o)
                if c.include: self.classes.append(c)

    @property
    def include(self):
        return self.funcs or self.classes

    @property
    def func_names(self): return self.funcs.attrgot('name')

    @property
    def class_names(self): return self.classes.attrgot('name')