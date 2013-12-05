from copy import deepcopy
from pypetree.utils.hashable_numpy_array import *
from pypetree.model.point_cloud import *


class TreeNode:

    def __init__(self, id, pos, points=None, level=None, parent=None,
                 children=None, radius=None, radii=None):
        self.id = id
        self.pos = pos
        self.points = points if points else set()
        self.level = level
        self.parent = parent
        self.children = children if children else set()
        self.radius = radius
        self.radii = radii if radii else set()

    def is_branching_node(self):
        return len(self.children) > 1

    def is_tip_node(self):
        return len(self.children) == 0

    def is_root_node(self):
        return self.parent is None

    
class TreeModel(dict):

    def __init__(self):
        self.k_idx = 0
        self.pos_to_k = {} # harray -> k
        self.max_level = -1

    def add_node(self, pos, points=None, level=None, parent=None,
                children=None, radius=None):
        node = TreeNode(id=self.k_idx, pos=pos, points=points,
                        level=level, parent=parent,
                        children=children, radius=radius)
        self[self.k_idx] = node
        self.pos_to_k[pos] = self.k_idx
        self.k_idx += 1
        if level is not None: self.max_level = max(level, self.max_level)
        return node

    def get_or_add_node_at_pos(self, pos):
        if pos in self.pos_to_k:
            return self[self.pos_to_k[pos]]
        else:
            return self.add_node(pos)

    # This will remove every recursively all children found from k' cut point;
    # it is only safe way to remove nodes from the tree.
    # The cut point is the node where the cut will be initiated:
    #   * above: everything above k will be removed
    #   * k: above + k
    #   * nearest_down_branching: will go down to nearest branching and
    #     cut from there
    def cut(self, k, point='above'):

        assert point in ['above', 'including', 'down_nearest_branching']

        def visit_upward(k, visited=set()):
            for k in self[k].children:
                visited.add(k)
                visit_upward(k, visited)
            return visited

        start_cut = k
        if point == 'down_nearest_branching':
            if not self[start_cut].is_branching_node():
                while True:
                    parent = self[start_cut].parent
                    if not parent or self[parent].is_branching_node(): break
                    start_cut = self[start_cut].parent
            else:                # if the cutting point is a branching node,
                point = 'above'  # the user probably doesn't want to cut
                                 # from a lower point, so simply cut above


        if point in ['including', 'down_nearest_branching']:
            start_set = {start_cut}
        else:
            start_set = set()
        visited = visit_upward(start_cut, start_set)

        for l in visited:
            parent = self[l].parent
            if parent in self:
                self[parent].children.discard(l)
            del self[l]

        return visited

    def remove_orphan_nodes(self):
        for k, node in deepcopy(self.items()):
            if node.parent is None and not node.children:
                del self[k]

    def get_number_of_tips(self):
        return sum([1 for node in self.values() if not node.children])

    # smooth all branches from tip to root with a moving average
    # returns a new TreeModel intance
    def smooth(self, w):
        if w <= 1: return deepcopy(self)
        L = TreeModel()
        m = int(w / 2)
        # a 'branch' here is a full path from tip to source (in K)
        for k, node in self.items():
            if not node.children:
                branch_ks = [k]
                branch_pos = [self[k].pos]
                while node.parent is not None:
                    kj = node.parent
                    branch_ks.append(kj)
                    branch_pos.append(self[kj].pos)
                    node = self[kj]
                ext_branch_pos = [branch_pos[0]] * m + branch_pos + \
                                                         [branch_pos[-1]] * m
                smooth_pos = []
                for i in range(len(branch_pos)): # not sure here..
                    smooth_pos.append(harray(mean(ext_branch_pos[i:i+w],
                                                  axis=0)))
                smooth_pos[0] = branch_pos[0]
                smooth_pos[-1] = branch_pos[-1]
                assert len(smooth_pos) == len(branch_pos) == len(branch_ks)
                # smooth branch reconstruction
                child_l = None
                for i, pos in enumerate(smooth_pos):
                    l = L.get_or_add_node_at_pos(pos).id
                    if child_l is not None:
                        L[child_l].parent = l
                        L[l].children.add(child_l)
                    L[l].radius = self[branch_ks[i]].radius
                    child_l = l
        #L.set_levels()
        return L

    def set_levels(self):

        def visit_upward(k, level):
            self[k].level = level
            self.max_level = max(level, self.max_level)
            for k in self[k].children:
                visit_upward(k, level + 1)

        root = None
        for k, node in self.items():
            if node.is_root_node():
                root = k
                break
        assert root is not None
        visit_upward(root, 0)

    def calibrate_user_measurement_marker(self, p):
        # map end user-defined marker (green) to closest model segment point
        candidates = [] # (dist, q, k)
        for k, node in self.items():
            if self[k].is_root_node(): continue
            #candidates.append((dist(p, node.pos), node.pos, node.radius, k))
            q = closest_point_on_segment_from_point(p, node.pos,
                                               self[node.parent].pos)
            d = dist(self[k].pos, q) / dist(self[k].pos,
                                            self[self[k].parent].pos)
            radius = self[k].radius + ((self[self[k].parent].radius -
                                                       self[k].radius) * d)
            candidates.append((dist(p, q), q, radius, k))
        return min(candidates)[1:] # discard distance

    def find_interpolated_measurement_markers(self, mm_user_spheres, n_markers):
        # (1) find total length
        assert len(mm_user_spheres) == 2
        b = self[mm_user_spheres[0].mm_node].level > \
            self[mm_user_spheres[1].mm_node].level
        high = (mm_user_spheres[0 if b else 1].get_position(),
                self[mm_user_spheres[0 if b else 1].mm_node])
        low = (mm_user_spheres[1 if b else 0].get_position(),
               self[mm_user_spheres[1 if b else 0].mm_node])
        assert not high[1].is_root_node() and not low[1].is_root_node()
        total_dist = 0
        k = high[1].id
        last_pos = None
        while True:
            if self[k].parent is None: return None
            if k == high[1].id:
                total_dist += dist(high[0], self[self[k].parent].pos)
                last_pos = high[0]
            elif k == low[1].id:
                total_dist += dist(low[0], self[k].pos)
            else:
                total_dist += dist(self[k].pos, self[self[k].parent].pos)
            if k == low[1].id: break
            k = self[k].parent
        # (2) interpolate markers
        marker_dist = total_dist / (n_markers - 1)
        marker_dist_accum = 0
        markers = [] # (pos, radius)'s, from high to low
        k = high[1].id
        while True:
            if k != low[1].id:
                seg_end_pos = self[self[k].parent].pos
            else:
                seg_end_pos = low[0]
            dist_last_pos_to_seg_end_pos = dist(last_pos, seg_end_pos)
            if marker_dist_accum + dist_last_pos_to_seg_end_pos < marker_dist:
                marker_dist_accum += dist_last_pos_to_seg_end_pos
                last_pos = seg_end_pos
            else:
                remaining_marker_dist = marker_dist - marker_dist_accum
                r = remaining_marker_dist / dist_last_pos_to_seg_end_pos
                marker_pos = last_pos + ((seg_end_pos - last_pos) * r)
                d = (dist(self[k].pos, marker_pos) /
                     dist(self[k].pos, self[self[k].parent].pos))
                marker_radius = self[k].radius + ((self[self[k].parent].radius -
                                                   self[k].radius) * d)
                markers.append((marker_pos, marker_radius))
                last_pos = marker_pos
                marker_dist_accum = 0
                if len(markers) >= n_markers - 2:
                    break
                continue
            if k == low[1].id: break
            k = self[k].parent
        return markers[::-1] # invert from low to high

    def save(self, fn):
        f = open(fn, 'w')
        f.write('node_id,parent_node_id,x,y,z,radius\n')
        for k, node in self.items():
            f.write('%d,%s,%f,%f,%f,%f\n' %
                    (k, node.parent if node.parent is not None else '',
                     node.pos[0], node.pos[1], node.pos[2], node.radius))
        f.close()

    def load(self, fn):
        f = open(fn)
        header = f.readline()
        assert header.strip() == 'node_id,parent_node_id,x,y,z,radius'
        parents = {}
        for line in f:
            if not line.strip(): continue
            node = line.split(',')
            k = int(node[0])
            pos = harray([float(v) for v in node[2:5]])
            parent = int(node[1]) if node[1] else None
            self[k] = TreeNode(k, pos, parent=parent, radius=float(node[5]))
            if parent is not None:
                parents[k] = parent
        for k, parent in parents.items():
            self[parent].children.add(k)
        f.close()
        print 'size of smallest segment: %f' % self.get_size_of_smallest_segment()

    def get_dimensions(self):
        low = array((float('inf'), float('inf'), float('inf')))
        hi = array((float('-inf'), float('-inf'), float('-inf')))
        for k, node in self.items():
            for i in range(3):
                low[i] = min(low[i], node.pos[i])
                hi[i] = max(hi[i], node.pos[i])
        return hi - low

    def get_surface(self):
        total_surf = 0
        for k, node in self.items():
            if node.parent is None: continue
            parent = self[node.parent]
            avg_radius = (node.radius + parent.radius) / 2
            axis = node.pos - parent.pos
            surf = 2 * pi * avg_radius * linalg.norm(axis)
            total_surf += surf
        return total_surf

    def get_number_of_levels(self):
        if self.max_level < 0: self.set_levels()
        return self.max_level

    def get_size_of_smallest_segment(self):
        min_size = float('inf')
        for node in self.values():
            if node.parent is None: continue
            min_size = min(min_size, dist(node.pos, self[node.parent].pos))
        return min_size
