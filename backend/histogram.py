class Histogram:
    def __init__(self, d=None):
        if d and 'histcounts' in d:
            self.histcounts = d['histcounts']
        elif d:
            self.histcounts = d
        else:
            self.histcounts = {}

    def update(self, x):
        if x in self.histcounts:
            self.histcounts[x] += 1
        else:
            self.histcounts[x] = 1

    def get(self):
        return self.histcounts

    def max(self):
        return max(self.histcounts.keys())

    def __repr__(self):
        return str(self.histcounts)

    def combine(self, histogram):
        for (k,v) in histogram.get().items():
            if k in self.histcounts:
                self.histcounts[k] += v
            else:
                self.histcounts[k] = v

def combine_histograms(hist_list):
    # Creates a combined histogram of all the histograms in hist_list which may
    # be Histograms, dictionaries or arrays.
    def process(k,v):
        if k in combined_hist:
            combined_hist[k] += v
        else:
            combined_hist[k] = v
    combined_hist = {}
    for hist in hist_list:
        if isinstance(hist, Histogram):
            for (k,v) in hist.get().items(): process(k,v)
        elif isinstance(hist, dict):
            for (k,v) in hist.items(): process(k,v)
        else:
            for(k, v) in enumerate(hist):
                process(k, v)
    return Histogram(combined_hist)

def histograms2array(hist_list):
    # Creates a list of count lists from a list of histograms. All the count
    # lists have the same length, filling with zeros where needed.
    histarray = []
    if not hist_list:
        pass
    elif isinstance(hist_list[0], Histogram):
        keymax = max(hist.max() for hist in hist_list) + 1
    else:
        keymax = max(max(hist.keys) for hist in hist_list) + 1
    for hist in hist_list:
        L = [0]*keymax
        if isinstance(hist, Histogram):
            hist = hist.get()
        for (k,v) in hist.items():
            L[k] = v
        histarray.append(L)
    return histarray

def combine_histogram_lists(hist_list):
    # Combine list of histogram lists [L0,L1...] into a list of histograms, [H0,H1...]:
    # H0 is the combined histogram for L0[0], L1[0]..., H1 combines L0[1], L1[1], etc.
    # There is one L-list for each core and one H-histogram for each electoral system.
    nsys = len(hist_list[0])
    combined_list = []
    for i in range(nsys):
        h = combine_histograms(h[i] for h in hist_list)
        combined_list.append(h)
    return combined_list

