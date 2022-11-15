import numpy as np
class Histo_int:
    def __init__(self, shape=1):
        self.n = 0
        self.shape = shape
        self.counts = [{} for _ in range(self.shape)]
        
    def update(self, x):
        if isinstance(x, int):
            x = [x]
        for k in range(self.shape):
            xk = x[k]
            if xk in self.counts[k]:
                self.counts[xk] += 1
            else:
                self.counts[xk] = 1
        self.n += 1
                
    def combine(self, histo):
        for k in range(self.shape):
            for (x,count) in histo.counts[k].items():
                if x in self.counts[k]:
                    self.counts[k] += histo.counts[k]
                else:
                    self.counts[k] = histo.counts[k]
        self.n += histo.n
            
    def get_quantile(self, x):
        pos = round(x*self.n)
        q = np.zeros(self.shape)
        for k in range(self.shape):
            cum = np.cumsum(self.counts[k].values())
            keys = list(self.counts[k].keys())
            q[k] = keys[np.searchsorted(cum, pos, side='right')]
        return self.q

class Histo_bins:
    def __init__(self, minimum, maximum, shape=1):
        self.n = 0
        self.shape = shape
        self.edges = np.linspace(minimum, maximum, 50)
        self.bins = np.zeros((shape, len(self.edges)), int)
        
    def update(self, x):
        if isinstance(x, (float,int)):
            x = [x]
        for k in range(self.shape):
            xk = x[k]
            i = np.searchsorted(self.edges, xk, side='right')
            i = min(i, len(self.edges))
            self.bins[k,i] += 1
        self.n += 1

    def combine(self, histo):
        self.bins += histo.bins

    def get_quantile(self, x):
        pos = x*self.n
        q = np.zeros(self.shape)
        for k in range(self.shape):
            cum = np.cumsum(self.bins[k])
            q[k] = np.interp(pos, cum, self.edges)
        return q