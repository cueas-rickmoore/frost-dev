
import numpy as N

from matplotlib import pyplot

from .base import Base2DPlot 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DEFAULT_TITLE = 'Histogram'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Histogram(Base2DPlot):
        
    def __call__(self, data, **kwargs):
        if not self.plot_initialized: self.newPlot(**kwargs)

        data = data[N.where(N.isfinite(data))]
        data_min = kwargs.get('data_min', data.min())
        data_max = kwargs.get('data_max', data.max())

        # plot parameters
        num_bins = kwargs.get('num_bins', None)
        bin_incr = kwargs.get('bin_incr', None)
        if num_bins is None:
            if bin_incr is None: bin_incr = 10
            num_bins = int((data_max - data_min) / bin_incr) + 1
        if bin_incr is None:
            bin_incr = ((data_max - data_min) / num_bins)
        show_counts = kwargs.get('show_counts', False)

        bins = N.arange(data_min,(num_bins+1)*bin_incr, bin_incr)
        counts, bins, rectangles = pyplot.hist(data, bins)

        # create the histogram
        if show_counts:
            max_count = max(counts)
            max_index = list(counts).index(max_count)
            max_height = rectangles[max_index].get_height()
            y_offset = max_height * 0.02

            for indx in range(len(counts)):
                count = counts[indx]
                rectangle = rectangles[indx]
                min_x = rectangle.get_x()
                x = min_x + (rectangle.get_width() / 2.)
                y = rectangle.get_height() + y_offset
                pyplot.text(x, y, '%d'%count, ha='center', va='bottom')

