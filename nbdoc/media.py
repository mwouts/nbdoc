# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/media.ipynb (unless otherwise specified).

__all__ = ['HTMLdf', 'HTMLEscape', 'ImageSave', 'ImagePath']

# Cell
from nbconvert.preprocessors import Preprocessor
from fastcore.xtras import Path
from html.parser import HTMLParser

# Cell
class HTMLdf(HTMLParser):
    """HTML Parser that finds a dataframe."""
    df = False
    scoped = False

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            for k,v in attrs:
                if k == 'scoped': self.scoped=True

    def handle_data(self, data):
        if '.dataframe' in data and self.scoped:
            self.df=True

    def handle_endtag(self, tag):
        if tag == 'style': self.scoped=False

    @classmethod
    def search(cls, x):
        parser = cls()
        parser.feed(x)
        return parser.df

# Cell
class HTMLEscape(Preprocessor):
    """
    Place HTML in a codeblock and surround it with a <HTMLOutputBlock> component.
    """
    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type =='code':
            outputs = []
            for o in cell.outputs:
                if o.get('data') and o['data'].get('text/html'):
                    cell.metadata.html_output = True
                    html = o['data']['text/html']
                    cell.metadata.html_center = False if HTMLdf.search(html) else True
                    o['data']['text/html'] = '```html\n'+html.strip()+'\n```'
        return cell, resources

# Cell
class ImageSave(Preprocessor):
    "Saves images stored as bytes in notebooks to disk."
    def preprocess(self, nb, resources):
        meta = resources.get('metadata', {})
        nb_name = meta.get('name')
        nb_path = meta.get('path')
        outfiles = resources.get('outputs')
        if nb_name and outfiles:
            resources['fmap'] = {}
            for k,v in outfiles.items():
                dest = Path(nb_path)/f'_{nb_name}_files/{k}'
                dest.parent.mkdir(exist_ok=True)
                dest.write_bytes(v)
                resources['fmap'][f'{k}'] = f'_{nb_name}_files/{k}'
        return nb, resources

class ImagePath(Preprocessor):
    "Changes the image path to the location where `ImageSave` saved the files."
    def preprocess_cell(self, cell, resources, index):
        fmap = resources.get('fmap')
        if fmap:
            for o in cell.get('outputs', []):
                fnames = o.get('metadata', {}).get('filenames', {})
                for k,v in fnames.items():
                    fnames[k] = fmap.get(v,v)
        return cell, resources