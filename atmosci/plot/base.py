
from cStringIO import StringIO

import numpy as N

from matplotlib import pyplot

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Base2DPlot(object):

    DEFAULT_CMAP = 'jet'
    DEFAULT_DPI = 100
    DEFAULT_FIGSIZE = (8,6)
    DEFAULT_LABEL_SIZE = 12
    DEFAULT_LINE_WIDTH = 0
    DEFAULT_SYMBOLS = ('o','s','^',(5,1,0),'d')
    DEFAULT_SYMSIZE = 20
    DEFAULT_TITLE_SIZE = 16
        
    def __init__(self, **kwargs):
        self.cmap = kwargs.get('cmap', self.DEFAULT_CMAP)
        self.dpi = kwargs.get('dpi', self.DEFAULT_DPI)
        self.fig_size = kwargs.get('fig_size', self.DEFAULT_FIGSIZE)
        self.line_width = kwargs.get('line_width', self.DEFAULT_LINE_WIDTH)
        self.label_size = kwargs.get('label_size', self.DEFAULT_LABEL_SIZE)
        self.show_grid = kwargs.get('show_grid', False)
        self.subtitle_size = kwargs.get('subtitle_size', None)
        self.symbols = kwargs.get('symbols', self.DEFAULT_SYMBOLS)
        self.symbol_size = kwargs.get('symbol_size', self.DEFAULT_SYMSIZE)
        self.title_size = kwargs.get('title_size', self.DEFAULT_TITLE_SIZE)
        self.x_label_size = kwargs.get('x_label_size', None)
        self.y_label_size = kwargs.get('y_label_size', None)

        self.called_labels_and_titles = False
        self.next_symbol = 0
        self.plot_initialized = False

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def asImage(self, image_format='PNG', tight_box=False):
        image = StringIO()
        if tight_box:
           self.figure.savefig(image, format=image_format),
                              bbox_inches='tight', pad_inches=0.0)
        else:
            self.figure.savefig(image, format=image_format)
        return image

    def newFigure(self, **kwargs):
        fig_size = kwargs.get('figsize', self.fig_size)
        dpi = kwargs.get('dpi', self.dpi)
        self.figure = pyplot.figure(figsize=fig_size, dpi=dpi)
        self.axis = pyplot.gca()

    def save(self, filepath, **kwargs):
        if not self.called_labels_and_titles:
            self.labelsAndTitles(**kwargs)
        pyplot.axes(self.axis)
        self.figure.savefig(filepath)

    def show(self, **kwargs):
        if not self.called_labels_and_titles:
            self.labelsAndTitles(**kwargs)
        pyplot.axes(self.axis)
        pyplot.ion()
        pyplot.show()

