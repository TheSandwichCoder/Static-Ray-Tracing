from Vector3 import Vec3

class Scene():
    def __init__(self, objects, lightsources, environmentLighting = Vec3(0,0,0)):
        self.objects = objects
        self.lights = lightsources
        self.envLighting = environmentLighting/255

    def getEnvironmentLight(self, vec):
        if self.envLighting.mag == 0:
            return self.envLighting

        return (self.envLighting * (vec.y+0.5)).clamp((0,0,0),(1,1,1))

