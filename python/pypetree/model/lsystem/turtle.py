from numpy import *

class Turtle:

    def __init__(self):
        self.T = eye(4) # transformation matrix
        self.stack = []

    def get_pos(self):
        return array([self.T[0][-1], self.T[1][-1], self.T[2][-1]])

    def get_dir(self):
        return dot(self.T, [0,1,0,0])[:3]

    def rotate_x(self, a):
        a = radians(a)
        self.T = dot(self.T, [[1, 0,      0,       0],
                              [0, cos(a), -sin(a), 0],
                              [0, sin(a), cos(a),  0],
                              [0, 0,      0,       1]])

    def rotate_y(self, a):
        a = radians(a)
        self.T = dot(self.T, [[cos(a),  0, sin(a), 0],
                              [0,       1, 0,      0],
                              [-sin(a), 0, cos(a), 0],
                              [0,       0, 0,      1]])

    def rotate_z(self, a):
        a = radians(a)
        self.T = dot(self.T, [[cos(a), -sin(a), 0, 0],
                              [sin(a), cos(a),  0, 0],
                              [0,      0,       1, 0],
                              [0,      0,       0, 1]])

    # around dir
    def rotate(self, a):
        a = radians(a)
        ux, uy, uz = self.get_dir()
        ux2, uy2, uz2 = ux**2, uy**2, uz**2
        self.T = dot(self.T, [[cos(a) + ux2 * (1 - cos(a)),
                               ux * uy * (1 - cos(a)) - uz * sin(a),
                               ux * uz * (1 - cos(a)) - uy * sin(a), 0],
                              [uy * ux * (1 - cos(a)) + uz * sin(a),
                               cos(a) + uy2 * (1 - cos(a)),
                               uy * uz * (1 - cos(a)) - ux * sin(a), 0],
                              [uz * ux * (1 - cos(a)) - uy * sin(a),
                               uz * uy * (1 - cos(a)) + ux * sin(a),
                               cos(a) + uz2 * (1 - cos(a)), 0],
                              [0, 0, 0, 1]])

    def translate(self, d):
        self.T += [[0, 0, 0, d[0]],
                   [0, 0, 0, d[1]],
                   [0, 0, 0, d[2]],
                   [0, 0, 0, 0   ]]

    def forward(self, d=1):
        self.translate(self.get_dir() * d)

    def push_matrix(self):
        self.stack.append(self.T.copy()) # copy is important!

    def pop_matrix(self):
        self.T = self.stack.pop()
