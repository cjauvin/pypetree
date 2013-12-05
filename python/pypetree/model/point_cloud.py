from __future__ import division
import sys
from collections import defaultdict
from scipy.spatial import *
import networkx as nx
from pypetree.utils.hashable_numpy_array import *
from pypetree.utils import *


def dist(p1, p2):
    return linalg.norm(p1 - p2)


# find the dimension with the largest span
def guess_point_cloud_height_dimension(P):
    return max([(max(P[:,dim]) - min(P[:,dim]), dim) for dim in [0,1,2]])[1]


# see http://www.softsurfer.com/Archive/algorithm_0102/
# algorithm_0102.htm#closest2D_Point_to_Line()
def closest_point_on_segment_from_point(p, p0, p1):
    v = p1 - p0
    w = p - p0
    c1 = dot(w, v)
    if c1 <= 0:
        return p0
    c2 = dot(v, v)
    if c2 <= c1:
        return p1
    b = c1 / c2
    return p0 + b * v


class GeodesicClipping:

    def __init__(self, P):
        self.P = P

    def nearest_neighbors(self, k, r):
        kdtree = cKDTree(self.P)
        dists, result = kdtree.query(self.P, k=k+1, distance_upper_bound=r)
        g = nx.Graph()
        for i, row in enumerate(result):
            for j, d in zip(row[1:], dists[i][1:]):
                if d == float('inf'): continue
                g.add_edge(i, j, weight=d)
        conn_graphs = nx.connected_component_subgraphs(g)
        self.N = sorted([(len(g.nodes()), g) for g in conn_graphs],
                        reverse=True)[0][1]
        self.source = self.N.nodes()[argmin(self.P[self.N.nodes(), 2])]

    def clip(self, d):
        self.G = nx.single_source_dijkstra_path(self.N, self.source)
        g = nx.Graph()
        P = set()
        print 'geodesic clipping..'
        for path in pbar(self.G.values()):
            if len(path) < 2: continue
            curr_dist = 0
            for p in range(1, len(path)): # from source (level 0) to i
                curr_dist += self.N[path[p-1]][path[p]]['weight']
                if curr_dist <= d:
                    g.add_edge(path[p-1], path[p])
                    P.add(harray(self.P[path[p-1]]))
                    P.add(harray(self.P[path[p]]))
                else:
                    break
        return vstack(P)

    
class QuantizedPointCloud():

    def __init__(self, P):
        self.P = P
        self.low_range = array([min(P[:,0]), min(P[:,1]), min(P[:,2])])
        self.hi_range = array([max(P[:,0]), max(P[:,1]), max(P[:,2])])
        self.bins = {} # harray -> set
        self.bin_size = None

    def quantize(self, bin_size, gauge=None):
        self.bin_size = bin_size
        self.bins = defaultdict(set)
        for i, p in pbar(enumerate(self.P), maxval=len(self.P), gauge=gauge):
            self[self.quantize_point(p)] = i

    def __len__(self):
        return len(self.bins)

    def get_bin_dims(self):
        return (self.quantize_point(self.hi_range) -
                self.quantize_point(self.low_range)) + 1

    def quantize_point(self, p):
        return harray((p - self.low_range) / self.bin_size, int)

    def unquantize_point(self, q):
        return harray(((q + 0.5) * self.bin_size) + self.low_range)

    def __getitem__(self, q):
        return self.bins[q]

    def __setitem__(self, q, item):
        self.bins[q].add(item)

    def __delitem__(self, q):
        del self.bins[q]

    def __iter__(self):
        for q in self.bins:
            yield q

    def downsample(self, bin_size, mode='bin_centroids',
                   gauge_popup=None, gauge_msgs=None):
        assert mode in ['bin_centroids', 'grid']
        gauge_popup.SetTitle(gauge_msgs[0])
        self.quantize(bin_size, gauge_popup.gauge)
        P = empty((len(self), 3))
        gauge_popup.SetTitle(gauge_msgs[1])
        for i, q in pbar(enumerate(self), maxval=len(self),
                         gauge=gauge_popup.gauge):
            if mode == 'grid':
                P[i] = self.unquantize_point(q)
            else:
                P[i] = mean(self.P[[j for j in self[q]]], axis=0)
        return P
