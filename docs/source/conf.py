# -*- coding: utf-8 -*-
import os
import sys

import sphinx_rtd_theme

thisdir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(thisdir, '../../src')))

# -- General configuration -----------------------------------------------------

extensions = [
    'jinjaapidoc',
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
]
if os.getenv('SPELLCHECK'):
    extensions += 'sphinxcontrib.spelling',
    spelling_show_suggestions = True
    spelling_lang = 'en_US'

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'pytwitcherapi'
copyright = u'2015, David Zuber'

version = '0.9.0'
release = '0.9.0'

exclude_patterns = ['_build']
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
htmlhelp_basename = 'pytwitcherapidoc'

# -- Options for LaTeX output --------------------------------------------------

latex_elements = {}

latex_documents = [
    ('index', 'pytwitcherapi.tex', u'pytwitcherapi Documentation',
     u'David Zuber', 'manual'),
]

# -- Autodoc Config -------------------------------------------------------

autoclass_content = 'class'  # include __init__ docstring
autodoc_member_order = 'bysource'
autodoc_default_flags = ['members', 'undoc-members', 'show-inheritance']


# -- Intersphinx Config ---------------------------------------------------
intersphinx_mapping = {'python': ('https://docs.python.org/2.7', None),
                       'requests': ('http://docs.python-requests.org/en/latest/', None),
                       'irc': ('https://pythonhosted.org/irc/', None)}

autosummary_generate = True

# -- Jinjaapidoc Config ---------------------------------------------------

jinjaapi_srcdir = os.path.abspath(os.path.join(thisdir, '..', '..', 'src'))
jinjaapi_outputdir = os.path.abspath(os.path.join(thisdir, 'reference'))
jinjaapi_nodelete = False
