import math

class Vec3:
    def __init__(self,x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vec = (x,y,z)
        self.mag = math.sqrt(x**2+ y**2 + z**2)

    def normalise(self):
        if self.mag == 0:
            return self.copy()
        return Vec3(self.x/self.mag, self.y/self.mag, self.z/self.mag)

    def copy(self):
        return Vec3(self.x, self.y, self.z)

    def dot(self, otherVec3):
        return self.x*otherVec3.x+self.y*otherVec3.y+self.z*otherVec3.z

    def multiply_vec(self, otherVec3):
        return Vec3(self.x*otherVec3.x, self.y*otherVec3.y, self.z*otherVec3.z)

    def clamp(self, lowerBound = (0,0,0), upperBound = (255,255,255)):
        return Vec3(min(max(self.x, lowerBound[0]), upperBound[0]),min(max(self.y, lowerBound[1]), upperBound[1]),min(max(self.z, lowerBound[2]), upperBound[2]))

    def set(self,x=False,y=False,z=False):
        if x:
            self.x = x
        if y:
            self.y = y
        if z:
            self.z = z

    def update_val(self):
        self.vec = (self.x, self.y, self.z)
        self.mag = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)



    def __add__(self, otherVec3):
        return Vec3(self.x+otherVec3.x, self.y+otherVec3.y, self.z+otherVec3.z)

    def __sub__(self, otherVec3):
        return Vec3(self.x-otherVec3.x, self.y-otherVec3.y, self.z-otherVec3.z)

    def __mul__(self, mag):
        return Vec3(self.x * mag, self.y * mag, self.z * mag)

    def __truediv__(self, mag):
        return Vec3(self.x / mag, self.y / mag, self.z / mag)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __abs__(self):
        return Vec3(abs(self.x), abs(self.y), abs(self.z))

    def __str__(self):
        return f"({self.x} {self.y} {self.z})"