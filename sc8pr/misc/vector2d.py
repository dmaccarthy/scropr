# Copyright 2015-2020 D.G. MacCarthy <https://dmaccarthy.github.io/sc8pr>
#
# This file is part of "sc8pr".
#
# "sc8pr" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "sc8pr" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "sc8pr".  If not, see <http://www.gnu.org/licenses/>.

from math import cos, sin, hypot, sqrt
from sc8pr import Renderable, Graphic, Canvas, CENTER
from sc8pr.geom import sigma, polar2d, transform2d, smallAngle, DEG
from sc8pr.shape import Arrow, Line


class Vector(Renderable):
    plot = None
    tail = 0, 0
    stroke = "red"
    weight = 3
    arrowShape = 16, 10
    contains = Graphic.contains

    def __init__(self, mag=None, direction=0, xy=None):
        if mag is None:
            self.mag, self.dir = polar2d(*xy)
        else:
            if mag < 0:
                self.dir = direction + 180
                self.mag = -mag
            else:
                self.dir = direction
                self.mag = mag
            self.dir = smallAngle(self.dir)

    def __str__(self):
        x, y = self.xy
        return "<{} {:.3g} @ {:.1f} ({:.3g}, {:.3g})>".format(type(self).__name__, self.mag, self.dir, x, y)

    @property
    def anchor(self): return CENTER

    @property
    def angle(self):
        p = self.plot
        return self.dir if (p is None or p.clockwise) else -self.dir

    @angle.setter
    def angle(self, a):
        p = self.plot
        self.dir = smallAngle(a if (p is None or p.clockwise) else -a)

    def rotate(self, angle, xy=None):
        if xy is None: xy = self.middle
        self.tail = transform2d(self.tail, rotate=angle, shift=xy, preShift=True)
        self.dir += angle

    @property
    def xy(self): return self.x, self.y

    @property
    def x(self): return self.mag * cos(self.dir * DEG)

    @property
    def y(self): return self.mag * sin(self.dir * DEG)

    def proj(self, u):
        "Return projection onto a vector or direction"
        u = Vector(1, u.dir if isinstance(u, Vector) else u)
        return (u * (self * u)).config(plot=self.plot)

    def __add__(self, other):
        xy = sigma(self.xy, other.xy)
        return Vector(xy=xy).config(plot=self.plot)

    def __sub__(self, other):
        return self + other * -1

    def __mul__(self, other):
        if isinstance(other, Vector):
            x1, y1 = self.xy
            x2, y2 = other.xy
            return x1 * x2 + y1 * y2
        else:
            return Vector(other * self.mag, self.dir).config(plot=self.plot)

    def __truediv__(self, x):
        return Vector(self.mag / x, self.dir).config(plot=self.plot)

    def shift(self, dx=0, dy=0):
        tx, ty = self.tail
        self.tail = tx + dx, ty + dy

    @property
    def middle(self):
        tx, ty = self.tail
        x, y = self.xy
        return tx + x/2, ty + y/2

    @middle.setter
    def middle(self, xy):
        cx, cy = self.middle
        self.shift(xy[0] - cx, xy[1] - cy)

    @property
    def tip(self):
        tx, ty = self.tail
        x, y = self.xy
        return tx + x, ty + y

    @tip.setter
    def tip(self, xy):
        tx, ty = self.tip
        self.shift(xy[0] - tx, xy[1] - ty)

    @property
    def units(self):
        "Calculate plot scales"
        plot = self.plot
        return (1, 1) if plot is None else plot.units

    @property
    def unit(self): return hypot(*self.units) / sqrt(2)

    @property
    def pos(self):
        c = self.middle
        p = self.plot
        return c if p is None else p.pixelCoords(c)

    @pos.setter
    def pos(self, xy):
        p = self.plot
        self.middle = xy if p is None else p.plotCoords(xy)

    def render(self):
        l = self.mag * self.unit
        shape = self.arrowShape
        if type(shape) is dict:
            if shape["fixed"]:
                shape = shape.copy()
                shape["width"] /= l
                shape["head"] /= l
            del shape["fixed"]
            a = Arrow(l, **shape).config(fill=self.fill, stroke=self.stroke, weight=self.weight)
        else:
            dx, dy = shape
            cv = Canvas((l, 2 * dy))
            y = cv.center[1]
            cv += Line((0, y), (l, y)).config(stroke=self.stroke, weight=self.weight)
            cv += Line((l - dx, y - dy), (l, y)).config(stroke=self.stroke, weight=self.weight)
            cv += Line((l - dx, y + dy), (l, y)).config(stroke=self.stroke, weight=self.weight)
            a = cv.snapshot()
        return a.image

    def style(self, n=1):
        "Preset drawing styles"
        self.config(fill="red", stroke="black", weight=1)
        if n == 1:
            self.arrowShape = {"width": 12, "head": 16, "flatness": 2, "fixed": True}
        else:
            self.arrowShape = {"width": 0.1, "head": 0.1, "flatness": 2, "fixed": False}
        return self