from __future__ import division
import progressbar as pb
from webcolors import *
from numpy import *


def pbar(it, maxval=None, gauge=None):
    if gauge is None:
        if maxval is not None:
            return pb.ProgressBar(term_width=40, maxval=maxval)(it)
        else:
            return pb.ProgressBar(term_width=40)(it)
    else:
        g_range = maxval if maxval else len(it)
        gauge.SetRange(g_range)
        
        class PbarGaugeIter:

            def __init__(self):
                self.inc = int(g_range * 5 / 100.0)
                self.i = 0

            def __iter__(self):
                return self

            def next(self):
                if self.i % self.inc == 0:
                    gauge.SetValue(self.i)
                    gauge.Update()
                self.i += 1
                return it.next()

        return PbarGaugeIter()


def name_to_rgb_float(name):
    return array(name_to_rgb(name)) / 255
