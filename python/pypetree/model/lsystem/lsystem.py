from pypetree.ui.world import PointCloud
from pypetree.model.tree_model import *
from turtle import *
import random as std_random
import numpy.random as np_random


USE_VPYTHON = False


# hashable dict
class hdict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))

    
class LSystemTree:

    # rules: {'X':'...'}
    def __init__(self, axiom, rules, n_iters, angle_mean_in_degrees,
                 angle_sd_in_degrees, init_seglen, init_segrad, seglen_scaling,
                 seglen_scaling_sd, segrad_scaling, segrad_scaling_sd, seed=None):

        try: seed = int(seed)
        except: seed = None
        std_random.seed(seed)
        self.struct_seed = seed        

        sequence = axiom
        for i in range(n_iters):
            rewrite = ''
            for c in sequence:
                rewrite += rules.get(c, c)
            sequence = rewrite            
        self.segments = set()
        seglen, segrad = init_seglen, init_segrad
        curr_seglen_scaling, curr_segrad_scaling = seglen_scaling, segrad_scaling
        
        turtle = Turtle()

        # build a tree structure
        self.K = TreeModel()

        if USE_VPYTHON: print sequence

        for c in sequence:

            delta = std_random.gauss(angle_mean_in_degrees, angle_sd_in_degrees)

            if c.upper() == 'F':
                if USE_VPYTHON:
                    vs.cylinder(pos=turtle.get_pos(), axis=turtle.get_dir() * seglen,
                                radius=segrad, color=(0.5,0.5,0.5))

                # update tree structure (K)
                pos1 = harray(turtle.get_pos())
                pos2 = pos1 + (turtle.get_dir() * seglen)
                k1 = self.K.get_or_add_node_at_pos(pos1).id
                k2 = self.K.get_or_add_node_at_pos(pos2).id
                self.K[k1].pos = pos1
                self.K[k1].radii.add(round(segrad, 5))
                self.K[k1].children.add(k2)
                self.K[k2].pos = pos2
                self.K[k2].radii.add(round(segrad * segrad_scaling, 5))
                if self.K[k2].parent is not None:
                    assert self.K[k2].parent == k1
                self.K[k2].parent = k1
                
                turtle.forward(seglen)

            elif c == '[':
                curr_seglen_scaling = std_random.gauss(seglen_scaling, seglen_scaling_sd)
                curr_segrad_scaling = std_random.gauss(segrad_scaling, segrad_scaling_sd)
                seglen *= curr_seglen_scaling
                segrad *= curr_segrad_scaling
                turtle.push_matrix()

            elif c == ']':
                seglen /= curr_seglen_scaling
                segrad /= curr_segrad_scaling
                turtle.pop_matrix()

            # around L/X (-)
            elif c.lower() in '^v':
                turtle.rotate_x(delta if c == 'v' else -delta)

            # around U/Y (|)
            elif c in '+-':
                turtle.rotate_y(delta if c == '+' else -delta)

            # around H/Z (/)
            elif c in '<>':
                turtle.rotate_z(delta if c == '>' else -delta)

            # around F
            elif c in '/\\':
                turtle.rotate(delta if c == '/' else -delta)

            elif c == '|':
                turtle.rotate_z(180)

        for k, node in self.K.items():
            avg_radius = sum([r for r in node.radii]) / len(node.radii)
            node.radius = avg_radius

    def sample(self, density, deviation, add_source_point=True, seed=None):

        try: seed = int(seed)
        except: seed = None
        np_random.seed(seed)
        self.sample_seed = seed
        points = set()
        for k, node in self.K.items():
            if node.parent is None: continue
            parent = self.K[node.parent]
            avg_radius = (node.radius + parent.radius) / 2
            axis = node.pos - parent.pos
            surf = 2 * pi * avg_radius * linalg.norm(axis)
            n = int(round(density * surf))
            p1 = parent.pos
            p2 = node.pos
            p = np_random.randn(3)
            r = cross(p-p1, p2-p1)
            r /= linalg.norm(r)
            s = cross(r, p2-p1)
            s /= linalg.norm(s)
            for i in range(n):
                theta = np_random.uniform(0, radians(360))
                d = np_random.uniform() # relative distance of the point, on line between p1 and p2
                t = p1 + d * axis
                interp_radius = (node.radius - parent.radius) * d + parent.radius
                if deviation:
                    interp_radius += np_random.exponential(deviation)
                q = harray([t[0] + interp_radius * cos(theta) * r[0] + interp_radius * sin(theta) * s[0],
                           t[1] + interp_radius * cos(theta) * r[1] + interp_radius * sin(theta) * s[1],
                           t[2] + interp_radius * cos(theta) * r[2] + interp_radius * sin(theta) * s[2]])
                points.add(q)
        if add_source_point:
            points.add((0,-0.01,0))
        self.P = vstack(points)

        
if __name__ == '__main__':

    from vpython_conf import *
    USE_VPYTHON = True
    #vs.scene.center = (0, 15 * 0.25, 0)

    def replace(rules, x, y):
        for head in rules:
            rules[head] = rules[head].replace(x, y)

    #rules = {'A': '[^FA][vFA][<FA][>FA]'} # ok
    #rules = {'F': 'F [+F] [-F] F [+F] -FF'} # ok
    #rules = {'A': '[^FA]++++[^FA]++++[^FA]'} # angle=30, ok
    #rules = {'A': '[^A]F[vA]F[<A][>A][+A]'}
    #rules = {'A': '[<FA]++[F]+[>FA]'}
    #rules = {'A': '[<FA][F][>FA]'}
    rules = {'A': '[<F]F[^F][>F]'}

    axiom = 'FA'
   
    m = LSystemTree(axiom=axiom, rules=rules,
                    n_iters=1, angle_mean_in_degrees=30,
                    angle_sd_in_degrees=0,
                    init_seglen=1, init_segrad=0.05,
                    seglen_scaling=0.65, segrad_scaling=0.8)

    vs_loop()
