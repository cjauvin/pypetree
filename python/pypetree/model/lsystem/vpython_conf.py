#!/usr/bin/python

from __future__ import division
import visual as vs
from numpy import *


scene_range_divider = 1.5 # 1.75


def adjust_view_angle():
    vs.scene.forward = vs.scene.forward.rotate(axis=(0,1,0), angle=math.radians(45))

    
def p2vs(p):
    return p[[0,2,1]]


def vs_loop():

    #pan_inc = 0.25
    #zoom_inc = array((0.25,0.25,0.25))
    pan_inc = 0.25
    zoom_inc = array((0.05,0.05,0.05))

    # for scene rotation with invariant light direction
    light_frame = vs.frame()
    for obj in vs.scene.lights:
        if isinstance(obj, vs.distant_light):
            obj.frame = light_frame # put distant lights in a frame
    prev_scene_forward = vs.vector(vs.scene.forward) # keep a copy of the old forward

    while True:

        if vs.scene.kb.keys:
            key = vs.scene.kb.getkey()

            if key == 'up':
                vs.scene.center = array(vs.scene.center) + array((0,pan_inc,0))
            elif key == 'down':
                vs.scene.center = array(vs.scene.center) + array((0,-pan_inc,0))
            elif key == 'left':
                vs.scene.center = array(vs.scene.center) + array((-pan_inc,0,0))
            elif key == 'right':
                vs.scene.center = array(vs.scene.center) + array((pan_inc,0,0))

            elif key == 'shift+up':
                vs.scene.range -= zoom_inc
            elif key == 'shift+down':
                vs.scene.range += zoom_inc

        if vs.scene.forward != prev_scene_forward:
            new = vs.scene.forward
            axis = vs.cross(prev_scene_forward, new)
            angle = new.diff_angle(prev_scene_forward)
            light_frame.rotate(axis=axis, angle=angle)
            prev_scene_forward = vs.vector(new)

    
if __name__ == '__main__':
    
    pass
