from mglg.graphics.shaders import FlatShader
from mglg.graphics.shape2d import Square, Circle
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
    
    # add a ball
    mass = 40
    size = 0.05, 0.08
    circle = Circle(win.context, prog, scale=size, 
                    fill_color=(0.9, 0.3, 0.3, 0.8))
    inertia = pymunk.moment_for_box(mass, size)
    cbody = pymunk.Body(mass, inertia)
    cbody.position = 0.2, 0.2
    cshape = pymunk.Poly.create_box(cbody, size=size)
    cshape.elasticity = 0.9
    cshape.friction = 0.1

    pivot = pymunk.constraint.PivotJoint(static_body, cbody, (0, 0), (0, 0))
    pivot.max_bias = 0
    pivot.max_force = 11
    #gear = pymunk.constraint.GearJoint(static_body, cbody, 0, 1.0)
    #gear.error_bias = 0
    #gear.max_bias = 0.1
    #gear.max_force = 1000

    space.add(cbody, cshape, pivot)

    # boundaries
    bbody = pymunk.Body(body_type=pymunk.Body.STATIC)
    lwall = pymunk.Segment(bbody, [-0.8, -0.5], [-0.8, 0.5], 0.05)
    rwall = pymunk.Segment(bbody, [0.8, 0.5], [0.8, -0.5], 0.05)
    bwall = pymunk.Segment(bbody, [-0.8, -0.5], [0.8, -0.5], 0.05)
    twall = pymunk.Segment(bbody, [-0.8, 0.5], [0.8, 0.5], 0.05)
    lwall.elasticity = rwall.elasticity = bwall.elasticity = twall.elasticity = 0.9
    space.add(bbody, lwall, rwall, bwall, twall)

    dev = MpDevice(TestSerial())
    with dev:
        while True:
            data = dev.read()
            if data is not None:
                # forward
                d1 = data[-1]/4096.0
                tank_control_body.angular_velocity = (d1[2] - d1[3]) * 16
                # get angle (radians)
                current_angle = tank_control_body.angle
                diff_vel = (d1[0] - d1[1]) * 2
                nv = diff_vel * cos(current_angle)
                nw = diff_vel * sin(current_angle)
                tank_control_body.velocity = (nv, nw)
            
            for i in range(4):
                space.step(1/(60*4))
            sqr.position = tank_body.position
            sqr.rotation = tank_body.angle * 180/pi
            sqr.draw(cam)

            circle.position = cbody.position
            circle.rotation = cbody.angle * 180/pi
            circle.draw(cam)
            win.flip()
            if win.dt > 0.02: print(win.dt)

