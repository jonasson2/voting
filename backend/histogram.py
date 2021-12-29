import numpy as np
from math import prod

class Histogram:
    def __init__(self):
        self.histcounts = {}        

    def update(self, x):
        if x in self.histcounts:
            self.histcounts[x] += 1
        else:
            self.histcounts[x] = 1

    def get(self):
        return self.histcounts

def combine_counts(hist_list):
    combined_hist = {}
    for hist in hist_list:
        for (k,v) in hist.items():
            if k in combined_hist:
                combined_hist[k] += v
            else:
                combined_hist[k] = v
    return combined_hist
