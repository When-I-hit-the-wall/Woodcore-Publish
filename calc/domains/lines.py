"""Straight lines without ends, given as a point and an angle -- the construction aids a drawing is laid out with (issue #18), the position plan's first. Pure geometry, no project, no Qt, no file.

The plan stores an aid as an axis without bubbles is stored, `{point, angle}` in the units of its sheet, y down, the angle in degrees clockwise from the right and within (-90, 90] -- so `plan.axis_segment`, which crosses a line with the window shown, draws and snaps to it as it does an axis. What is new here is how an aid is made: horizontal, vertical, through two points, or parallel to another line at a distance.
"""

import math


def normal_angle(angle):
    """An angle of a line without direction, within (-90, 90]: a line at 135° is the line at -45°."""
    a = math.fmod(float(angle), 180.0)
    if a <= -90:
        a += 180
    elif a > 90:
        a -= 180
    return a + 0.0


def through(a, b):
    """The line through the points `a` and `b`: (a, its angle); None where they are one point."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if math.hypot(dx, dy) < 1e-9:
        return None
    return (float(a[0]), float(a[1])), normal_angle(math.degrees(math.atan2(dy, dx)))


def direction(angle):
    a = math.radians(angle)
    return math.cos(a), math.sin(a)


def foot(point, origin, angle):
    """The point of the line (`origin`, `angle`) nearest `point`."""
    ux, uy = direction(angle)
    t = (point[0] - origin[0]) * ux + (point[1] - origin[1]) * uy
    return origin[0] + t * ux, origin[1] + t * uy


def parallel_at(origin, angle, distance, side):
    """The line parallel to (`origin`, `angle`) at `distance` from it, on the side of the point `side`: (its point, the same angle). A side on the line itself takes the normal's own side."""
    ux, uy = direction(angle)
    nx, ny = -uy, ux
    if (side[0] - origin[0]) * nx + (side[1] - origin[1]) * ny < 0:
        nx, ny = -nx, -ny
    d = abs(float(distance))
    return (origin[0] + d * nx, origin[1] + d * ny), normal_angle(angle)
