# -*- coding: utf-8 -*-
#
# Monad documentation build configuration file.
import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, PROJECT_DIR)
import smonad

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
]

source_suffix = '.rst'

master_doc = 'index'

project = u'smonad'
copyright = u'2012-2014, Philip Xu'

version = '%d.%d' % smonad.__version__
release = smonad.VERSION

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'agogo'
# use RTD new theme
RTD_NEW_THEME = True

htmlhelp_basename = 'Monaddoc'

latex_documents = [
    ('index', 'SMonad.tex', u'SMonad Documentation',
     u'Philip Xu', 'manual'),
]

man_pages = [
    ('index', 'smonad', u'SMonad Documentation',
     [u'Philip Xu'], 1)
]

texinfo_documents = [
    ('index', 'SMonad', u'smonad Documentation',
     u'Philip Xu', 'SMonad', smonad.__doc__,
     'Miscellaneous'),
]
