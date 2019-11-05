from mglg.graphics.shaders import FlatShader
from mglg.graphics.shape2d import Square, square_vertices
from mglg.graphics.camera import Camera
import pymunk

# see https://github.com/slembcke/Chipmunk2D/blob/master/demo/Tank.c
# for emulating top-down physics
# essentially, need a pivot joint + gear joint to emulate linear, angular friction

if __name__ == '__main__':
    from toon.input import MpDevice
    from test import TestSerial
    from projection import height_ortho
    from window import ExpWindow as Window
    from math import pi, cos, sin
    win = Window()

    cam = Camera(projection=height_ortho(win.width, win.height))

    space = pymunk.Space()
    space.gravity = 0, 0 # top-down physics
    #space.sleep_time_threshold = 0.5 # things sleep after 500ms

    static_body = space.static_body # for later

    # what we control
    tank_control_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    tank_control_body.position = 0.1, 0
    # what is indirectly controlled via joints
    mass = 10 # arbitrary units
    size = 0.15, 0.1 # screen units
    inertia = pymunk.moment_for_box(mass, size)
    tank_body = pymunk.Body(mass, inertia)
    #tank_body.position = 0.1, 0 # start in center of screen

    prog = FlatShader(win.context)
    sqr = Square(win.context, prog, scale=size, 
                 fill_color=(0.7, 0.9, 0.2, 1))

    tank_collider = pymunk.Poly.create_box(tank_body, size=size)
    tank_collider.elasticity = 0.0
    tank_collider.friction = 0.7 # ???


    pivot = pymunk.constraint.PivotJoint(tank_control_body, tank_body, (0, 0), (0, 0))
    pivot.max_bias = 0 # disable joint correction
    pivot.max_force = 10000.0 # "linear friction"

    gear = pymunk.constraint.GearJoint(tank_control_body, tank_body, 0, 1.0)
    gear.error_bias = 0 # try to fully correct joint each step
    gear.max_bias = 1.2 # limit angular correction rate
    gear.max_force = 50000.0 # "angular friction"

    space.add(tank_control_body, tank_body, tank_collider, pivot, gear)
    
    dev = MpDevice(TestSerial())
    with dev:
        while True:
            data = dev.read()
            if data is not None:
                # forward
                d1 = data[-1]/4096.0
                tank_control_body.angular_velocity = (d1[2] - d1[3]) * 4
                # get angle (radians)
                current_angle = tank_control_body.angle
                diff_vel = d1[0] - d1[1]
                nv = diff_vel * cos(current_angle)
                nw = diff_vel * sin(current_angle)
                tank_control_body.velocity = (nv, nw)
            space.step(1/60)
            sqr.position = tank_body.position
            print(tank_control_body.position)
            sqr.rotation = tank_body.angle * 180/pi
            sqr.draw(cam)
            win.flip()

