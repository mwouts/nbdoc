# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/mdx.ipynb (unless otherwise specified).

__all__ = ['InjectMeta', 'StripAnsi', 'InsertWarning', 'RmEmptyCode', 'MetaflowTruncate', 'UpdateTags',
           'MetaflowSelectSteps', 'WriteTitle', 'CleanFlags', 'CleanMagics', 'Black', 'black_mode', 'CatFiles',
           'BashIdentify', 'CleanShowDoc', 'get_mdx_exporter']

# Cell
from nbconvert.preprocessors import Preprocessor
from nbconvert import MarkdownExporter
from nbconvert.preprocessors import TagRemovePreprocessor
from nbdev.imports import get_config
from traitlets.config import Config
from pathlib import Path
import re, uuid
from fastcore.basics import AttrDict
from .media import ImagePath, ImageSave, HTMLEscape
from black import format_str, Mode

# Cell
_re_meta= r'^\s*#(?:cell_meta|meta):\S+\s*[\n\r]'

# Cell
class InjectMeta(Preprocessor):
    """
    Allows you to inject metadata into a cell for further preprocessing with a comment.
    """
    pattern = r'(^\s*#(?:cell_meta|meta):)(\S+)(\s*[\n\r])'

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == 'code' and re.search(_re_meta, cell.source, flags=re.MULTILINE):
            cell_meta = re.findall(self.pattern, cell.source, re.MULTILINE)
            d = cell.metadata.get('nbdoc', {})
            for _, m, _ in cell_meta:
                if '=' in m:
                    k,v = m.split('=')
                    d[k] = v
                else: print(f"Warning cell_meta:{m} does not have '=' will be ignored.")
            cell.metadata['nbdoc'] = d
        return cell, resources

# Cell
_re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class StripAnsi(Preprocessor):
    """Strip Ansi Characters."""

    def preprocess_cell(self, cell, resources, index):
        for o in cell.get('outputs', []):
            if o.get('name') and o.name == 'stdout':
                o['text'] = _re_ansi_escape.sub('', o.text)
        return cell, resources

# Cell
def _get_cell_id(id_length=36):
    "generate random id for artifical notebook cell"
    return uuid.uuid4().hex[:id_length]

def _get_md_cell(content="<!--- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! Instead, edit the notebook w/the location & name as this file.-->"):
    "generate markdown cell with content"
    cell = AttrDict({'cell_type': 'markdown',
                     'id': f'{_get_cell_id()}',
                     'metadata': {},
                     'source': f'{content}'})
    return cell

# Cell
class InsertWarning(Preprocessor):
    """Insert Autogenerated Warning Into Notebook after the first cell."""
    def preprocess(self, nb, resources):
        nb.cells = nb.cells[:1] + [_get_md_cell()] + nb.cells[1:]
        return nb, resources

# Cell
def _emptyCodeCell(cell):
    "Return True if cell is an empty Code Cell."
    if cell['cell_type'] == 'code':
        if not cell.source or not cell.source.strip(): return True
    else: return False


class RmEmptyCode(Preprocessor):
    """Remove empty code cells."""
    def preprocess(self, nb, resources):
        new_cells = [c for c in nb.cells if not _emptyCodeCell(c)]
        nb.cells = new_cells
        return nb, resources

# Cell
class MetaflowTruncate(Preprocessor):
    """Remove the preamble and timestamp from Metaflow output."""
    _re_pre = re.compile(r'([\s\S]*Metaflow[\s\S]*Validating[\s\S]+The graph[\s\S]+)(\n[\s\S]+Workflow starting[\s\S]+)')
    _re_time = re.compile('\d{4}-\d{2}-\d{2}\s\d{2}\:\d{2}\:\d{2}.\d{3}')

    def preprocess_cell(self, cell, resources, index):
        if re.search('\s*python.+run.*', cell.source) and 'outputs' in cell:
            for o in cell.outputs:
                if o.name == 'stdout':
                    o['text'] = self._re_time.sub('', self._re_pre.sub(r'\2', o.text)).strip()
        return cell, resources

# Cell
class UpdateTags(Preprocessor):
    """
    Create cell tags based upon comment `#cell_meta:tags=<tag>`
    """

    def preprocess_cell(self, cell, resources, index):
        root = cell.metadata.get('nbdoc', {})
        tags = root.get('tags', root.get('tag')) # allow the singular also
        if tags: cell.metadata['tags'] = cell.metadata.get('tags', []) + tags.split(',')
        return cell, resources

# Cell
class MetaflowSelectSteps(Preprocessor):
    """
    Hide Metaflow steps in output based on cell metadata.
    """
    re_step = r'.*\d+/{0}/\d+\s\(pid\s\d+\).*'

    def preprocess_cell(self, cell, resources, index):
        root = cell.metadata.get('nbdoc', {})
        steps = root.get('show_steps', root.get('show_step'))
        if re.search('\s*python.+run.*', cell.source) and 'outputs' in cell and steps:
            for o in cell.outputs:
                if o.name == 'stdout':
                    final_steps = []
                    for s in steps.split(','):
                        found_steps = re.compile(self.re_step.format(s)).findall(o['text'])
                        if found_steps:
                            final_steps += found_steps + ['...']
                    o['text'] = '\n'.join(final_steps)
        return cell, resources

# Cell
class WriteTitle(Preprocessor):
    """Modify the code-fence with the filename upon %%writefile cell magic."""
    pattern = r'(^[\S\s]*%%writefile\s)(\S+)\n'

    def preprocess_cell(self, cell, resources, index):
        m = re.match(self.pattern, cell.source)
        if m:
            filename = m.group(2)
            ext = filename.split('.')[-1]
            cell.metadata.magics_language = f'{ext} title="{filename}"'
            cell.metadata.script = True
            cell.metadata.file_ext = ext
            cell.metadata.filename = filename
            cell.outputs = []
        return cell, resources

# Cell
_tst_flags = get_config()['tst_flags'].split('|')

class CleanFlags(Preprocessor):
    """A preprocessor to remove Flags"""
    patterns = [re.compile(r'^#\s*{0}\s*'.format(f), re.MULTILINE) for f in _tst_flags]

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == 'code':
            for p in self.patterns:
                cell.source = p.sub('', cell.source).strip()
        return cell, resources

# Cell
class CleanMagics(Preprocessor):
    """A preprocessor to remove cell magic commands and #cell_meta: comments"""
    pattern = re.compile(r'(^\s*(%%|%).+?[\n\r])|({0})'.format(_re_meta), re.MULTILINE)

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == 'code':
            cell.source = self.pattern.sub('', cell.source).strip()
        return cell, resources

# Cell
black_mode = Mode()

class Black(Preprocessor):
    """Format code that has a cell tag `black`"""
    def preprocess_cell(self, cell, resources, index):
        tags = cell.metadata.get('tags', [])
        if cell.cell_type == 'code' and 'black' in tags:
            cell.source = format_str(src_contents=cell.source, mode=black_mode).strip()
        return cell, resources

# Cell
class CatFiles(Preprocessor):
    """Cat arbitrary files with %cat"""
    pattern = '^\s*!'

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == 'code' and re.search(self.pattern, cell.source):
            cell.metadata.magics_language = 'bash'
            cell.source = re.sub(self.pattern, '', cell.source).strip()
        return cell, resources

# Cell
class BashIdentify(Preprocessor):
    """A preprocessor to identify bash commands and mark them appropriately"""
    pattern = re.compile('^\s*!', flags=re.MULTILINE)

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == 'code' and self.pattern.search(cell.source):
            cell.metadata.magics_language = 'bash'
            cell.source = self.pattern.sub('', cell.source).strip()
        return cell, resources

# Cell
_re_showdoc = re.compile(r'^ShowDoc', re.MULTILINE)


def _isShowDoc(cell):
    "Return True if cell contains ShowDoc."
    if cell['cell_type'] == 'code':
        if _re_showdoc.search(cell.source): return True
    else: return False


class CleanShowDoc(Preprocessor):
    """Ensure that ShowDoc output gets cleaned in the associated notebook."""
    _re_html = re.compile(r'<HTMLRemove>.*</HTMLRemove>', re.DOTALL)

    def preprocess_cell(self, cell, resources, index):
        "Convert cell to a raw cell with just the stripped portion of the output."
        if _isShowDoc(cell):
            all_outs = [o['data'] for o in cell.outputs if 'data' in o]
            html_outs = [o['text/html'] for o in all_outs if 'text/html' in o]
            if len(html_outs) != 1:
                return cell, resources
            cleaned_html = self._re_html.sub('', html_outs[0])
            cell = AttrDict({'cell_type':'raw', 'id':cell.id, 'metadata':cell.metadata, 'source':cleaned_html})

        return cell, resources

# Cell
def get_mdx_exporter(template_file='ob.tpl'):
    """A mdx notebook exporter which composes many pre-processors together."""
    c = Config()
    c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell", "hide")
    c.TagRemovePreprocessor.remove_all_outputs_tags = ("remove_output", "remove_outputs", "hide_output", "hide_outputs")
    c.TagRemovePreprocessor.remove_input_tags = ('remove_input', 'remove_inputs', "hide_input", "hide_inputs")
    pp = [InjectMeta, WriteTitle, CleanMagics, BashIdentify, MetaflowTruncate,
          MetaflowSelectSteps, UpdateTags, InsertWarning, TagRemovePreprocessor, CleanFlags, CleanShowDoc, RmEmptyCode,
          StripAnsi, Black, ImageSave, ImagePath, HTMLEscape]
    c.MarkdownExporter.preprocessors = pp
    tmp_dir = Path(__file__).parent/'templates/'
    tmp_file = tmp_dir/f"{template_file}"
    if not tmp_file.exists(): raise ValueError(f"{tmp_file} does not exist in {tmp_dir}")
    c.MarkdownExporter.template_file = str(tmp_file)
    return MarkdownExporter(config=c)