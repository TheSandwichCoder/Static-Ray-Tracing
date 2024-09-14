from Vector3 import Vec3

def clamp(val, lowerBound, upperBound):
    return max(min(val, upperBound), lowerBound)

def isInRange(value, lowerBound=0, upperBound=1):
    return lowerBound < value < upperBound



# --------OBJECTS----------
class Object():
    def __init__(self, pos, size, color, emmisionStrength, reflectivity, refraction):
        self.pos = pos
        self.size = size
        self.color = color
        self.normalisedColor = color/255
        self.emit = emmisionStrength
        self.shininess = reflectivity
        self.refIndex = refraction

class Sphere(Object):
    def __init__(self, pos, size, color, emmisionStrength=0, reflectivity=0, refraction=1):
        super().__init__(pos, size, color, emmisionStrength, reflectivity, refraction)

    def get_SDF(self, position):
        return (position-self.pos).mag-self.size

    def get_normal(self, position):
        return (position-self.pos).normalise()

    def scale(self, scaleVal, scalePos = False):
        self.size *= scaleVal

        if scalePos:
            self.pos *= scaleVal


class Capsule(Object):
    def __init__(self, startpos, endpos, size, color, emmisionStrength=0, reflectivity=0, refraction = 1):
        super().__init__((startpos+endpos)/2, size, color, emmisionStrength, reflectivity, refraction)
        self.startPos = startpos
        self.endPos = endpos
        self.dir = endpos-startpos
        self.length = self.dir.mag
        self.normDir = self.dir.normalise()

    def get_SDF(self, position):
        vecFromStart = (position - self.startPos)
        dottedThing = self.normDir.dot(vecFromStart/self.length)

        if dottedThing <= 0:
            return (position-self.startPos).mag - self.size

        elif dottedThing >= 1:
            return (position-self.endPos).mag - self.size

        else:
            nearest = self.startPos + self.dir*dottedThing

            return (position-nearest).mag - self.size

    def get_normal(self, position):
        vecFromStart = (position - self.startPos)
        dottedThing = self.normDir.dot(vecFromStart / self.length)

        if dottedThing <= 0:
            return (position - self.startPos).normalise()

        elif dottedThing >= 1:
            return (position - self.endPos).normalise()

        else:
            nearest = self.startPos + self.dir * dottedThing
            return (position - nearest).normalise()

    def scale(self, scaleVal, scalePos = False):
        self.size *= scaleVal

        if scalePos:
            self.pos *= scaleVal
            self.startPos *= scaleVal
            self.endPos *= scaleVal
            self.dir = self.endPos - self.startPos
            self.length = self.dir.mag

class Box(Object):
    def __init__(self, startPos, rotation, size, color, emmisionStrength=0, reflectivity=0, refraction = 1):
        super().__init__((startPos + size/2), size, color, emmisionStrength, reflectivity, refraction)
        self.startPos = startPos
        self.rotation = rotation

        self.x_axis_vec = Vec3(size.x,0,0)
        self.y_axis_vec = Vec3(0,size.y,0)
        self.z_axis_vec = Vec3(0,0,size.z)

        self.x_axis_norm = Vec3(1, 0, 0)
        self.y_axis_norm = Vec3(0, 1, 0)
        self.z_axis_norm = Vec3(0, 0, 1)

    def get_SDF(self, position):
        relVec = (position - self.startPos)
        # print(relVec)
        dot_x = clamp(self.x_axis_norm.dot(relVec/self.size.x),0,1)
        dot_y = clamp(self.y_axis_norm.dot(relVec/self.size.y),0,1)
        dot_z = clamp(self.z_axis_norm.dot(relVec/self.size.z),0,1)



        if isInRange(dot_x) and isInRange(dot_y) and isInRange(dot_z):
            return -min(((0.5-abs(dot_x-0.5))*self.size.x), ((0.5-abs(dot_y-0.5))*self.size.y), ((0.5-abs(dot_z-0.5))*self.size.z))

        closestRelPos = self.size.multiply_vec(Vec3(dot_x, dot_y, dot_z))

        closestPoint = self.startPos + closestRelPos

        return (closestPoint-position).mag

    def get_normal(self, position):
        relVec = (position - self.startPos)

        # the -0.5 normalises the dot to -0.5 to 0.5
        dot_x = self.x_axis_norm.dot(relVec / self.size.x) - 0.5
        dot_y = self.y_axis_norm.dot(relVec / self.size.y) - 0.5
        dot_z = self.z_axis_norm.dot(relVec / self.size.z) - 0.5

        nearestFace = max(abs(dot_x), abs(dot_y), abs(dot_z))
        normalVec = Vec3(0,0,0)

        if nearestFace == abs(dot_x):
            if dot_x > 0:
                normalVec += self.x_axis_norm
            else:
                normalVec -= self.x_axis_norm

        if nearestFace == abs(dot_y):
            if dot_y > 0:
                normalVec += self.y_axis_norm
            else:
                normalVec -= self.y_axis_norm

        if nearestFace == abs(dot_z):
            if dot_z > 0:
                normalVec += self.z_axis_norm
            else:
                normalVec -= self.z_axis_norm

        return normalVec.normalise()

    def scale(self, scaleVal, scalePos = False):
        self.size *= scaleVal
        if scalePos:
            self.x_axis_vec *= scaleVal
            self.y_axis_vec *= scaleVal
            self.z_axis_vec *= scaleVal

            self.startPos *= scaleVal
            self.pos *= scaleVal





class Plane(Object):
    def __init__(self, y_index, color, emmisionStrength=0, reflectivity=0):
        super().__init__(Vec3(0,y_index,0), 1, color, emmisionStrength, reflectivity, 1)

    def get_SDF(self, position):
        return position.y - self.pos.y

    def get_normal(self, position):
        return Vec3(0,1,0)

    def scale(self, scaleVal, scalePos=False):
        pass

    def get_vector_to_plane(self, rayPos, rayVec):
        if rayVec.y >= 0:
            return Vec3(0,0,0)

        y_mag = (rayPos.y - self.pos.y)/abs(rayVec.y)
        return rayVec * y_mag

def abs_min(val1, val2):
    if val1 < 0 and val2 < 0:
        return max(val1, val2) # -10, -15, returned -10
    return min(val1, val2)

def abs_max(val1, val2):
    if val1 < 0 and val2 < 0:
        return min(val1, val2)
    return max(val1, val2)

def mergeFunc_add(obj1, obj2, pos):
    return min(obj1.get_SDF(pos), obj2.get_SDF(pos))

def mergeFunc_intersect(obj1, obj2, pos):
    return max(obj1.get_SDF(pos), obj2.get_SDF(pos))

def mergeFunc_sub(obj1, obj2, pos):
    return max(obj1.get_SDF(pos), -obj2.get_SDF(pos))


mergeFuncDict = {
    "add":mergeFunc_add,
    "sub":mergeFunc_sub,
    "int":mergeFunc_intersect,
}

class MergedObjects(Object):
    def __init__(self, object1, object2, pos,size, color, mergeType="add", emmisionStrength=0, reflectivity=0, refraction=1):
        super().__init__(pos, size, color, emmisionStrength, reflectivity, refraction)
        self.obj1 = object1
        self.obj2 = object2
        self.mergeType = mergeType
        self.mergeFunc = mergeFuncDict[mergeType]

        self.obj1.scale(size, True)
        self.obj2.scale(size, True)

    def get_SDF(self, position):
        relPosition = position - self.pos
        return self.mergeFunc(self.obj1, self.obj2, relPosition)

    def scale(self, scaleVal, scalePos = False):
        self.obj1.scale(scaleVal, scalePos)
        self.obj2.scale(scaleVal, scalePos)

    def get_normal(self, position):
        relPosition = position - self.pos
        dist_to_obj1 = self.obj1.get_SDF(relPosition)
        dist_to_obj2 = self.obj2.get_SDF(relPosition)

        sign_value = 1
        if abs(dist_to_obj1) < abs(dist_to_obj2):
            closerObject = self.obj1
            closerDistance = dist_to_obj1
        else:
            closerObject = self.obj2
            closerDistance = dist_to_obj2

        if closerDistance < 0:
            sign_value = -1

        return closerObject.get_normal(relPosition) * sign_value








