# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/convert.ipynb (unless otherwise specified).

__all__ = ['nb2md', 'parallel_nb2md', 'nbdoc_build']

# Cell
import os, sys
from .mdx import get_mdx_exporter
from typing import Union
from nbdev.export import nbglob
from nbconvert.exporters import Exporter
from fastcore.all import Path, parallel, call_parse, bool_arg

# Cell
def nb2md(fname:Union[str, Path], exp:Exporter):
    "Convert a notebook in `fname` to a markdown file."
    file = Path(fname)
    assert file.name.endswith('.ipynb'), f'{str(fname)} is not a notebook.'
    assert file.is_file(), f'file {str(fname)} not found.'
    print(f"converting: {str(file)}")
    try:
        o,r = exp.from_filename(fname)
        file.with_suffix('.md').write_text(o)
        return True
    except Exception as e:
        print(e)
        return False

# Cell
def parallel_nb2md(basedir:Union[Path,str], exp:Exporter, recursive=True, force_all=False, n_workers=None, pause=0):
    "Convert all notebooks in `dir` to markdown files."
    files = nbglob(basedir, recursive=recursive).filter(lambda x: not x.name.startswith('Untitled'))
    if len(files)==1:
        force_all = True
        if n_workers is None: n_workers=0
    if not force_all:
        # only rebuild modified files
        files,_files = [],files.copy()
        for fname in _files:
            fname_out = fname.with_suffix('.md')
            if not fname_out.exists() or os.path.getmtime(fname) >= os.path.getmtime(fname_out):
                files.append(fname)
    if len(files)==0: print("No notebooks were modified.")
    else:
        if sys.platform == "win32": n_workers = 0
        passed = parallel(nb2md, files, n_workers=n_workers, exp=exp,  pause=pause)
        if not all(passed):
            msg = "Conversion failed on the following:\n"
            print(msg + '\n'.join([f.name for p,f in zip(passed,files) if not p]))

# Cell
@call_parse
def nbdoc_build(
    srcdir:str=None,  # A directory of notebooks to convert to docs recursively, can also be a filename.
    force_all:bool_arg=False, # Rebuild even notebooks that havent changed
    n_workers:int=None,  # Number of workers to use
    pause:float=0.5  # Pause time (in secs) between notebooks to avoid race conditions
):
    "Build the documentation by converting notebooks in `srcdir` to markdown"
    parallel_nb2md(basedir=srcdir,
                   exp=get_mdx_exporter(),
                   recursive=True,
                   force_all=force_all,
                   n_workers=n_workers,
                   pause=pause)