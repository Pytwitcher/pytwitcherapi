import os

_here = os.path.dirname(__file__)
SNIPPET_DIR = os.path.abspath(os.path.join(
    _here, '..', '..', 'docs', 'source', 'snippets'))


def get_snippet_path(snippetfile):
    return os.path.join(SNIPPET_DIR, snippetfile)


def execute_snippet(snippetfile):
    snippetfile = get_snippet_path(snippetfile)
    with open(snippetfile) as f:
        code = compile(f.read(), snippetfile, 'exec')
        exec(code, globals(), locals())
