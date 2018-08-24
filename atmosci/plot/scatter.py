
from .base import Base2DPlot

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ScatterPlot(Base2DPlot):
        
    def _plot_data(self, x, y, data, **kwargs):
        marker = kwargs.get('marker', kwargs.get('symbol', None))
        if marker is None: marker = self.nextMarker()

        self.axis.scatter(x, y, c=data,
                          vmin=kwargs.get('data_min',N.nanmin(data)),
                          vmax=kwargs.get('data_max',N.nanmax(data)),
                          cmap=kwargs.get('cmap',self.cmap), marker=marker,
                          s=kwargs.get('symbol_size',self.symbol_size),
                          linewidths=kwargs.get('line_width',self.line_width)
                         )

