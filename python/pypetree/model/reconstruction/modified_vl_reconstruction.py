from __future__ import division
import time
from copy import *
from numpy import *
import networkx as nx
from pypetree.utils.hashable_numpy_array import *
from collections import namedtuple, defaultdict
from scipy.spatial import *
from pypetree.model.tree_model import *
from pypetree.model.point_cloud import dist
from pypetree.utils import *

class ModifiedVerroustLazarusReconstruction:

    def __init__(self, P):
        self.P = P

    def compute_nearest_neighbors(self, k, r):
        start = time.time()
        kdtree = cKDTree(self.P)
        dists, result = kdtree.query(self.P, k=k+1, distance_upper_bound=r)
        self.N_full = nx.Graph()
        avg_pts_min_dist = 0
        for i, row in enumerate(result):
            if dists[i][1] < float('inf'): avg_pts_min_dist += dists[i][1]
            for j, d in zip(row[1:], dists[i][1:]):
                if d == float('inf'): continue
                self.N_full.add_edge(i, j, weight=d)
        avg_pts_min_dist /= len(self.N_full.nodes())
        print 'Average min dist between points: %f (over %d edges)' % \
              (avg_pts_min_dist, len(self.N_full.edges()))
        print 'NN compute time: %f seconds' % (time.time() - start)
        self.find_nn_connected_components()

    # KDTree.query_ball_tree impl (much slower!)
    def compute_nearest_neighbors_in_radius(self, r):
        start = time.time()
        kdtree1 = KDTree(self.P)
        kdtree2 = KDTree(self.P)
        result = kdtree1.query_ball_tree(kdtree2, r)
        self.N_full = nx.Graph()
        for i, i_nns in enumerate(result):
            for j in i_nns:
                if i == j: continue
                d = dist(self.P[i], self.P[j])
                self.N_full.add_edge(i, j, weight=d)
        print time.time() - start
        print len(self.N_full.edges())
        self.find_nn_connected_components()

    def find_nn_connected_components(self):
        start = time.time()
        conn_graphs = nx.connected_component_subgraphs(self.N_full)
        self.N_components = [g for n, g in sorted([(len(g.nodes()), g)
                                                   for g in conn_graphs],
                                                   reverse=True)]
        self.N = self.N_components[0] # biggest single component
        print 'NN components compute time: %f seconds' % (time.time() - start)

    def get_connectivity_infos(self):
        return len(self.N_components), len(self.N), nx.density(self.N_full)

    def compute_shortest_paths(self, ydim):
        start = time.time()
        self.source = self.N.nodes()[argmin(self.P[self.N.nodes(), ydim])]
        self.shortest_paths = nx.single_source_dijkstra_path(self.N,
                                                             self.source)
        self.max_path_len = max(nx.single_source_dijkstra_path_length(self.N,
                                                          self.source).values())
        print 'G compute time: %f seconds' % (time.time() - start)

    def compute_level_sets(self, n_levels=None, level_size=None,
                   dist_cap=float('inf'), min_connected_component_size=5):
        start = time.time()
        level_sets = defaultdict(set) # level -> set of point indexes
        self.P_dist = {} # used for extrement segment extension
        self.P_to_level = {}
        self.P_to_component = {}
        self.level_start_points = defaultdict(set) # used for volume recon
        self.G = nx.Graph()

        assert n_levels or level_size
        if n_levels:
            level_size = min(dist_cap, self.max_path_len) / n_levels
        else:
            n_levels = int(round(min(dist_cap, self.max_path_len) / level_size))

        for path in self.shortest_paths.values():
            if len(path) < 2: continue
            curr_dist = 0
            level = None
            for p in range(1, len(path)): # from source (level 0) to i
                i, j = path[p-1], path[p]
                w = self.N[i][j]['weight']
                curr_dist += self.N[i][j]['weight']
                self.G.add_edge(i, j, weight=w)
                if curr_dist > dist_cap: break
                level = int(curr_dist / level_size)
                if level == n_levels: level = n_levels - 1
                level_sets[level].add(j)
                self.P_dist[j] = curr_dist
            level_sets[0].add(path[0])
            self.P_dist[path[0]] = 0 # should be source point

        ls_recomputation_needed = True
        while ls_recomputation_needed:
            ls_recomputation_needed = False
            self.P_to_level = {}
            filtered_ls = {}
            filtered_lev_idx = 0
            # filtered_ls: filter empty LSes, and set indexes from 0 to N
            for level, points in sorted(level_sets.items()):
                if not points: continue
                filtered_ls[filtered_lev_idx] = points
                filtered_lev_idx += 1
            for level, points in filtered_ls.items():
                N_level = self.N.subgraph(points)
                components = nx.connected_component_subgraphs(N_level)
                for comp in components:
                    if len(comp.nodes()) < min_connected_component_size:
                        ls_recomputation_needed = True
                        for i in comp.nodes(): filtered_ls[level].remove(i)
                        if level > 0: level -= 1
                        else: level += 1
                        for i in comp.nodes(): filtered_ls[level].add(i)
                        level_sets = filtered_ls
                        break
                    for i in comp.nodes(): # this will be used when no
                        self.P_to_level[i] = level # ls_recomp is needed at all
                if ls_recomputation_needed: break

        # finally, LS content is fixed
        self.level_sets = defaultdict(set)
        for i, level in self.P_to_level.items():
            self.level_sets[level].add(i)

        for level, points in self.level_sets.items():
            N_level = self.N.subgraph(points)
            components = nx.connected_component_subgraphs(N_level)
            for comp in components:
                assert len(comp.nodes()) >= min_connected_component_size
                for i in comp.nodes():
                    self.P_to_component[i] = comp

        self.P_to_level[self.source] = -1
        for edge in self.G.edges():
            i, j = edge
            # should we only consider those with a level dist of 1?
            if abs(self.P_to_level[i] - self.P_to_level[j]) == 1:
            #if self.P_to_level[i] != self.P_to_level[j]:
                if self.P_to_level[i] > self.P_to_level[j]:
                    self.level_start_points[self.P_to_level[i]].add(i)
                else:
                    self.level_start_points[self.P_to_level[j]].add(j)
        self.P_to_level[self.source] = 0

        for level in self.level_sets:
            if not self.level_start_points[level]:
                print 'warning: level %d has no start points' % level

        print 'S compute time: %f seconds' % (time.time() - start)

        return len(self.level_sets.keys())

    def segmentation(self):

        self.K = TreeModel()
        self.K_to_P = defaultdict(list) # ki -> list of (i, d)'s
        self.P_to_K = {} # pi -> (ki, d)

        self.level_to_graph = [None for _ in range(len(self.level_sets))]
        self.level_to_segment_graphs = [None for _ in
                                        range(len(self.level_sets))]

        for level, points in self.level_sets.items():
            N_level_inter = self.N.subgraph(points)
            segment_nodes_list = nx.connected_components(N_level_inter)

            self.level_to_graph[level] = N_level_inter
            self.level_to_segment_graphs[level] = \
              nx.connected_component_subgraphs(N_level_inter)

            for segment_nodes in segment_nodes_list:
                segment_centroid = harray(mean(self.P[[segment_nodes]], axis=0))
                node = self.K.add_node(pos=segment_centroid,
                                      points=set(segment_nodes), level=level)
                max_dist = float('-inf')
                avg_dist = 0
                for j in segment_nodes:
                    d = dist(segment_centroid, self.P[j])
                    max_dist = max(max_dist, d)
                    avg_dist += d
                    self.K_to_P[node.id].append((j, d))
                    assert j not in self.P_to_K
                    self.P_to_K[j] = (node.id, d)
                # initial radius estimation (can be refined with
                # volume_reconstruction)
                avg_dist /= len(segment_nodes)
                node.radius = avg_dist

    def skeleton_reconstruction(self, use_greedy_search=True,
                               extend_end_segments=True):
        for k in self.K:
            if self.K[k].level == 0: continue
            potential_k_parents = [] # list of (dist, potential_k_parent)'s
            found_k_parent = False
            for i, dist_ki in self.K_to_P[k]:
                # travel from k toward source, via one of its belonging paths
                for j in self.shortest_paths[i][::-1]:
                    if j not in self.P_to_K: continue
                    l, dist_lj = self.P_to_K[j]
                    if self.K[l].level >= self.K[k].level: continue
                    dist_kl = dist(self.K[k].pos, self.K[l].pos)
                    cost = dist_ki + dist_kl + dist_lj
                    potential_k_parents.append((cost, l))
                    if use_greedy_search:
                        # for full search (takes really longer),
                        # comment out these two lines (not sure it
                        # makes sense though!)
                        found_k_parent = True
                        break
                if found_k_parent:
                    break
            #assert potential_k_parents
            if not potential_k_parents:
                print "warning: couldn't find a parent for skeleton node %s" % k
                continue
            k_parent = sorted(potential_k_parents)[0][1]
            self.K[k].parent = k_parent
            self.K[k_parent].children.add(k)

        self.K.remove_orphan_nodes()

        if extend_end_segments:

            # more precise method, derived from:
            # http://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html
            for k, node in self.K.items():

                if not node.children:
                    # find point with max dist from source
                    p_max_dist = [float('-inf'), None]
                    for i in node.points:
                        if self.P_dist[i] > p_max_dist[0]:
                            p_max_dist[0] = self.P_dist[i]
                            p_max_dist[1] = i
                    p_max_dist = self.P[p_max_dist[1]]
                    x1 = self.K[node.parent].pos
                    x2 = node.pos
                    x0 = p_max_dist
                    s = -dot((x1 - x0), (x2 - x1)) / (linalg.norm(x2 - x1) ** 2)
                    v = x1 + (x2 - x1) * s
                    self.K[k].pos = v

                if node.parent is None:
                    p_min_dist = [float('inf'), None] # should be the src point?
                    for i in node.points:
                        if self.P_dist[i] < p_min_dist[0]:
                            p_min_dist[0] = self.P_dist[i]
                            p_min_dist[1] = i
                    p_min_dist = self.P[p_min_dist[1]]
                    first_child_k = list(node.children)[0]
                    x1 = self.K[first_child_k].pos
                    x2 = node.pos
                    x0 = p_min_dist
                    s = -dot((x1 - x0), (x2 - x1)) / (linalg.norm(x2 - x1) ** 2)
                    v = x1 + (x2 - x1) * s
                    self.K[k].pos = v

            # simpler method (find and use extreme point)
            #     for k, node in self.K.items():

            #         if not node['children']:
            #             # find point with max dist from source
            #             max_dist_pt = (float('-inf'), -1)
            #             for i in node['points']:
            #                 max_dist_pt = max(max_dist_pt, (self.P_dist[i], i))
            #             self.K[k]['pos'] = self.P[max_dist_pt[1]]

            #         if node['parent'] is None:
            #             # find point with min dist from source
            #             min_dist_pt = (float('inf'), -1)
            #             for i in node['points']:
            #                 min_dist_pt = min(min_dist_pt, (self.P_dist[i], i))
            #             self.K[k]['pos'] = self.P[min_dist_pt[1]]

    def prune_skeleton(self):

        # return False if any point "higher" than source_level is found
        # while visiting the space of G upward, starting at i
        def can_reach_upper_level(i, source_level, visited=set()):
            i_dist = self.P_dist[i]
            for _, j in self.G.edges(i):
                if self.P_dist[j] <= i_dist or j in visited: continue
                visited.add(j)
                assert self.P_to_level[j] >= source_level
                if self.P_to_level[j] > source_level:
                    return True
                if can_reach_upper_level(j, source_level, visited):
                    return True
            return False

        false_tips = set()
        for k, node in self.K.items():
            if self.K[k].is_tip_node():
                is_segment_terminal = True
                for i in node.points:
                    if can_reach_upper_level(i, node.level):
                        is_segment_terminal = False
                        break
                if not is_segment_terminal:
                    false_tips.add(k)
        for k in false_tips:
            self.K.cut(k, point='down_nearest_branching')

    def volume_reconstruction(self):

        for ki in self.K:
            if not self.K[ki].children:
                kj = ki
                while self.K[kj].parent is not None:
                    kj_start_points = self.level_start_points[self.K[kj].level] \
                      & self.K[kj].points
                    # if not, will use initial radius estimation (not good!)
                    if kj_start_points:
                        kj_to_parent_midpoint = mean((self.K[kj].pos,
                                        self.K[self.K[kj].parent].pos), axis=0)
                        radius = 0
                        for pi in kj_start_points:
                            radius += dist(self.P[pi], kj_to_parent_midpoint)
                        radius /= len(kj_start_points)
                        self.K[kj].radius = radius
                    kj = self.K[kj].parent

        # segment radius smoothing

        roots = set()
        for ki in self.K:
            if not self.K[ki].children:
                segment = {} # kj -> radius
                kj = ki
                while self.K[kj].parent is not None:
                    segment[kj] = self.K[kj].radius
                    if len(self.K[kj].children) > 1 or \
                        self.K[self.K[kj].parent].parent is None:
                        # flush segment
                        avg_segment_radius = sum(segment.values()) / len(segment)
                        for kk in segment:
                            self.K[kk].radius = avg_segment_radius
                        segment = {}
                    kj = self.K[kj].parent
            if self.K[ki].parent is None:
                roots.add(ki)

        # roots radius

        #print 'roots: %s' % roots
        for ki in roots:
            #assert self.K[ki].get('radius', None) is None
            rad = 0
            for kj in self.K[ki].children:
                rad += self.K[kj].radius
            rad /= len(self.K[ki].children)
            self.K[ki].radius = rad

        # decreasing radius smoothing

        need_smoothing = True
        while need_smoothing:
            need_smoothing = False
            for ki in self.K:
                if not self.K[ki].children:
                    kj = ki
                    prev_radius = None
                    while self.K[kj].parent is not None:
                        curr_radius = self.K[kj].radius
                        next_radius = self.K[self.K[kj].parent].radius
                        if curr_radius > next_radius:
                            need_smoothing = True
                            if prev_radius:
                                curr_radius = (prev_radius + next_radius) / 2
                            else:
                                curr_radius = next_radius
                            curr_radius -= (0.01 * curr_radius)
                            self.K[kj].radius = curr_radius
                        prev_radius = curr_radius
                        kj = self.K[kj].parent
