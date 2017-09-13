# Copyright 2015-2017 D.G. MacCarthy <http://dmaccarthy.github.io>
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


import pygame
from pygame.pixelarray import PixelArray
from sc8pr import LEFT, RIGHT
from sc8pr.util import rgba
from random import uniform, random
from math import sqrt


class Effect:
    "Base class for all surface effects"
    _time = None

    def time(self, zero, one):
        self._time = zero, one
        return self

    def transition(self, img, n):
        t0, t1 = self._time
        n = (n - t0) / (t1 - t0)
        return self.apply(img, 0 if n <= 0 else 1 if n >= 1 else n)

    def srfSize(self, img, size=False):
        srf = img if isinstance(img, pygame.Surface) else img.image
        return (srf, srf.get_size()) if size else srf


class ReplaceColor(Effect):
    "Replace one color by another"

    def __init__(self, color, replace=(0,0,0,0), dist=0):
        self.color1 = color
        self.color2 = replace
        self.dist = dist

    def apply(self, img, n=0):
        srf = self.srfSize(img)
        d = self.dist * (1 - n)
        pygame.PixelArray(srf).replace(self.color1, self.color2, d)
        return img


class Tint(Effect):
    "Adjust the color and/or transparency"

    def __init__(self, color=(255,255,255,0)):
        self.color = rgba(color)

    def apply(self, img, n=0):
        srf = self.srfSize(img)
        color = [round(c + (255 - c) * n) for c in self.color]
        srf.fill(color, None, pygame.BLEND_RGBA_MULT)
        return img


class Wipe(Effect):

    def __init__(self, flags=1): self.flags = flags

    @staticmethod
    def _dim(n, flags, w0):
        "Calculate 'wiped' position and size in one dimension"
        if flags:
            w = round(n * w0)
            dw = w0 - w
            x = dw if flags == RIGHT else 0 if flags == LEFT else dw//2
            return x, w
        return 0, w0

    @staticmethod
    def _apply(srf, pos, size, origSize):
        "Blit the visible subsurface onto a transparent background"
        img = pygame.Surface(origSize, pygame.SRCALPHA)
        img.blit(srf.subsurface(pos, size), pos)
        return img
       
    def apply(self, img, n=0):
        srf, size = self.srfSize(img, True)
        flags = self.flags 
        x, w = self._dim(n, flags & 3, size[0])
        y, h = self._dim(n, flags >> 2, size[1])
        return self._apply(srf, (x,y), (w,h), size)


class Squish(Wipe):

    @staticmethod
    def _apply(srf, pos, size, origSize):
        "Blit the scaled image onto a transparent background"
        srf = pygame.transform.smoothscale(srf, size)
        img = pygame.Surface(origSize, pygame.SRCALPHA)
        img.blit(srf, pos)
        return img


class MathEffect(Effect):
    "Effect based on y < f(x) or y > f(x)"

    def __init__(self, fill=(0,0,0,0), eqn=None):
        self.fill = rgba(fill)
        if eqn: self.eqn = eqn.__get__(self, self.__class__)

    def eqn(self, x, n, size):
        h = size[1]
        return uniform(n * h, h)

    def apply(self, img, n=0):
        "Modify image based on equation provided"
        srf, size = self.srfSize(img, True)
        h = size[1]
        pxa = PixelArray(srf)
        x = 0
        for pxCol in pxa:
            y = self.eqn(x, n, size)
            if type(y) is tuple: y, above = y
            else: above = True
            if type(y) is float: y = int(y)
            if above:
                if y < h - 1:
                    if y < 0: y = 0
                    pxCol[y:] = self.fill
            elif y > 0:
                if y > h: y = h
                pxCol[:y] = self.fill
            x += 1
        return srf


class PaintDrops(MathEffect):
    "Paint drop effect"

    def __init__(self, fill=(0,0,0,0), drops=64):
        self.fill = rgba(fill)
        self.side = drops > 0
        self.drops = [self.makeDrop() for i in range(abs(drops))]
        n = sum([d[0] for d in self.drops])
        for d in self.drops: d[0] /= n

    def eqn(self, x, n, size):
        "Calculate paint boundary"
        if not self.side: n = 1 - n
        w, h = size
        y = 0
        xc = 0
        for d in self.drops:
            r = d[0] * w / 2
            R = 1.1 * r
            xc += r
            dx = abs(x - xc)
            if dx <= R:
                dy = sqrt(R * R - dx * dx)
                Y = (h + R) * self.posn(n, *d[1:]) + dy - R
                if Y > y: y = Y
            xc += r
        return y, self.side

    def posn(self, n, t1, t2):
        "Calculate drop position"
        if n < t1: return 0
        elif n > t2: return 1
        return (n - t1) / (t2 - t1)

    @staticmethod
    def makeDrop():
        "Create random diameter, start and end time"
        t1 = uniform(0, 0.8)
        t2 = uniform(t1 + 0.1, 1)
        return [uniform(0.1,1), min(t1, t2), max(t1, t2)]


class PixelEffect(Effect):

    def apply(self, img, n):
        "Apply pixel-by-pixel effect"
        srf = self.srfSize(img)
        pxa = PixelArray(srf)
        x = 0
        for pxCol in pxa:
            for y in range(len(pxCol)):
                c = pxCol[y]
                px = self.pixel(n, x, y, c)
                if px != c: pxCol[y] = px
            x += 1
        return srf


class Dissolve(PixelEffect):

    def __init__(self, fill=(0,0,0,0)): self.fill = rgba(fill)

    def pixel(self, n, x, y, c):
        return self.fill if random() > n else c