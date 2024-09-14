import math
from Vector3 import Vec3
import objects as objectsLibrary
import random

FOV = 90
ScreenSize = (1280, 720)
ScreenSizeCenter = (ScreenSize[0]/2, ScreenSize[1]/2)

denoiseColor = (123,231, 92)

current_y_batch = 719
current_x_batch = 0

def fix_color(color):

    return color.clamp()

def getRandomVector():
    azi_angle = random.randint(0,628) / 100
    polar_angle = random.randint(0,314) / 100

    return Vec3(math.sin(polar_angle)*math.cos(azi_angle), math.sin(polar_angle)*math.sin(azi_angle), math.cos(polar_angle))

def getRefractVector(rayVec, normVec, n1, n2):
    relativeRefIndex = n1/n2

    cos_theta1 = -rayVec.dot(normVec)
    sin_theta1_squared = 1.0 - cos_theta1**2
    sin_theta2_squared = relativeRefIndex ** 2 * sin_theta1_squared

    if sin_theta2_squared > 1.0:
        return False

    cos_theta2 = math.sqrt(1.0-sin_theta2_squared)

    refVec = rayVec * relativeRefIndex + normVec * (relativeRefIndex * cos_theta1 - cos_theta2)
    return refVec.normalise()  # Normalize the refracted vector

# march step default : 50
def rayMarch(rayPos, rayVec, objects, marchSteps=500, printStuff=False):
    for i in range(marchSteps):
        objDistances = [obj.get_SDF(rayPos) for obj in objects]
        minDistance = min(objDistances)

        if printStuff:
            print(minDistance)

        if minDistance <= 0.0001:
            objIndex = objDistances.index(minDistance)
            return rayPos, objects[objIndex]
        elif minDistance > 10000:
            return False, None

        rayPos += (rayVec * minDistance)

    # additional plane check to prevent plane warping
    for obj in objects:
        if type(obj) == objectsLibrary.Plane:
            rayPos += obj.get_vector_to_plane(rayPos, rayVec)
            if obj.get_SDF(rayPos) <= 0.0001:
                return rayPos, obj

    return False, None

# ray marching through clear object
def rayMarchThroughObj(rayPos, rayVec, object, marchSteps=500):
    originalRayPos = rayPos.copy()

    distance = object.get_SDF(rayPos)
    if distance >= 0:
        return rayPos

    for i in range(marchSteps):
        distance = object.get_SDF(rayPos)
        if abs(distance) < 0.0001:

            return rayPos

        if abs(distance) >= 10000:
            print("distance val exceeded")
            anotherOGRayPos = originalRayPos.copy()
            return anotherOGRayPos

        rayPos += (rayVec * abs(distance))

    # uhhh something bad prob happened
    print("shit this isnt good")

    return rayPos

raySampleNum = 10
brightnessIndex = 4
brightnessDropoff = 1

# recursive ray trace
def getRayColor(rayPos, rayVec, scene, depth):
    rayHitObj, obj = rayMarch(rayPos, rayVec, scene.objects + scene.lights)

    if rayHitObj != False:

        if obj.emit > 0:  # the object is a light
            return obj.normalisedColor * obj.emit

        else:  # the object is an object
            if depth != 0:
                if obj.shininess > 0: # the object is shiny

                    normalVec = obj.get_normal(rayHitObj - rayVec*0.01)

                    reflectVector = (rayVec - (normalVec * (normalVec.dot(rayVec)) * 2)).normalise()

                    if obj.shininess < 1:
                        randomVector = getRandomVector()
                        if randomVector.dot(normalVec) < 0:
                            randomVector = -randomVector

                        reflectVector = (reflectVector + randomVector*(1-obj.shininess)).normalise()


                    reflectColor = getRayColor(rayHitObj + reflectVector, reflectVector, scene, depth-1)

                    return reflectColor.multiply_vec(obj.normalisedColor)

                if obj.refIndex != 1:
                    normalVec = obj.get_normal(rayHitObj)
                    refVec = getRefractVector(rayVec, normalVec,1, obj.refIndex)

                    if refVec != False:
                        newRayPos = rayMarchThroughObj(rayHitObj+rayVec, refVec, obj)
                        newNormalVec = -obj.get_normal(newRayPos)

                        exitVec = getRefractVector(refVec, newNormalVec, obj.refIndex, 1)

                        if exitVec != False:
                            BounceColor = getRayColor(newRayPos+refVec, exitVec, scene, depth-1)

                        else:
                            reflectVector = (refVec - (newNormalVec * (newNormalVec.dot(refVec)) * 2)).normalise()

                            BounceColor = getRayColor(rayHitObj + reflectVector, reflectVector, scene, depth - 1)

                        return obj.normalisedColor.multiply_vec(BounceColor)

                    else: #total internal reflection
                        reflectVector = (rayVec - (normalVec * (normalVec.dot(rayVec)) * 2)).normalise()

                        BounceColor = getRayColor(rayHitObj+reflectVector, reflectVector, scene, depth-1)

                        return BounceColor

                averageSampleColor = Vec3(0,0,0)
                for raySample in range(raySampleNum):
                    normalVec = obj.get_normal(rayHitObj)
                    randomVector = getRandomVector()

                    if normalVec.dot(randomVector) <= 0:
                        randomVector = -randomVector

                    BounceColor = getRayColor(rayHitObj+randomVector, randomVector, scene, depth-1)

                    averageSampleColor += BounceColor

                averageSampleColor /= brightnessIndex
                averageSampleColor *= brightnessDropoff

                return obj.normalisedColor.multiply_vec(averageSampleColor.clamp((0,0,0),(1,1,1)))

    return scene.getEnvironmentLight(rayVec)








class Camera:
    def __init__(self, pos):
        self.centerPos = pos
        self.relCenter = (ScreenSize[0]/2, ScreenSize[1]/2)
        self.focal_pos = Vec3(0,0,-600)

    def checkInIllumination(self, scene, pos, printStuff = False):
        for light in scene.lights:
            rayVec = (light.pos - pos).normalise()

            rayHitPos, obj = rayMarch(pos, rayVec, scene.objects+scene.lights, printStuff=printStuff)

            if rayHitPos != False and obj.emit > 0:
                return True

        return False

    def quickRenderSceneBatch(self, surface, scene, y_batch):
        for x in range(0,1280,3):
            pixelPos = Vec3(ScreenSizeCenter[0] - x, ScreenSizeCenter[1] - y_batch, 0)

            lightRayVec = (pixelPos - self.focal_pos).normalise()
            lightRayPosition = self.centerPos + lightRayVec

            hitPos, obj = rayMarch(lightRayPosition, lightRayVec, scene.objects+scene.lights)

            if hitPos != False:
                surface.set_at((x, y_batch), (obj.color).vec)


    def rayTraceRenderSceneBatch2(self, surface, scene, y_batch, bounceDepth, rerenderNum):
        global current_y_batch
        global current_x_batch
        current_y_batch = y_batch
        for x in range(1280):
            current_x_batch = x
            pixelPos = Vec3(ScreenSizeCenter[0] - x, ScreenSizeCenter[1] - y_batch, 0)

            lightRayVec = (pixelPos - self.focal_pos).normalise()
            lightRayPosition = self.centerPos + lightRayVec

            pixelColor = getRayColor(lightRayPosition, lightRayVec, scene, bounceDepth)

            previousPixelColor = surface.get_at((x, y_batch))
            previousPixelColorVec = Vec3(previousPixelColor[0], previousPixelColor[1], previousPixelColor[2])/255

            if pixelColor.mag != 0:
                if previousPixelColorVec.mag != 0:

                    surface.set_at((x, y_batch), ((pixelColor * (1/rerenderNum) + previousPixelColorVec * ((rerenderNum-1)/rerenderNum))*255).vec)
                else:
                    surface.set_at((x, y_batch), (pixelColor*255).vec)

    # ugly ass hard coded ray tracing (attempt 1)
    def rayTraceRenderSceneBatch(self, surface, scene, y_batch, rerenderNum):
        ray_num = 100
        brightnessMultiplier = 40
        for x in range(1280):
            pixelPos = Vec3(ScreenSizeCenter[0] - x, ScreenSizeCenter[1] - y_batch, 0)

            pixelColor = Vec3(0,0,0)

            lightRayVec = (pixelPos - self.focal_pos).normalise()
            lightRayPosition = self.centerPos + lightRayVec.copy()

            rayHitPos, obj = rayMarch(lightRayPosition, lightRayVec, scene.objects+scene.lights)

            if rayHitPos == False:
                if lightRayVec.y < 0:
                    y_mag = -(self.centerPos.y - scene.plane) / lightRayVec.y
                    hit_z = lightRayVec.z * y_mag
                    hit_x = lightRayVec.x * y_mag
                    floorPosition = Vec3(hit_x, scene.plane, hit_z)

                    for i in range(ray_num):
                        newRayVec = getRandomVector()
                        if newRayVec.y < 0:
                            newRayVec.y = abs(newRayVec.y)

                        newRayHitPos, newHitObj = rayMarch(floorPosition.copy(), newRayVec, scene.objects + scene.lights)

                        if not newRayHitPos or newHitObj.emit == 0: # pixel didnt hit a light
                            if self.checkInIllumination(scene, floorPosition):
                                pixelColor = Vec3(denoiseColor[0], denoiseColor[1], denoiseColor[2])


                            continue

                        pixelColor = newHitObj.color * newHitObj.emit
                        break
            else:
                if obj.emit > 0:
                    pixelColor = obj.color * obj.emit

                else:
                    normalVec = obj.get_normal(rayHitPos)
                    hit_num = 0
                    objHitColor = Vec3(0,0,0)
                    objHitEmit = 0

                    for i in range(ray_num):
                        newRayVec = getRandomVector()
                        if normalVec.dot(newRayVec) < 0:
                            newRayVec = -newRayVec

                        newRayHitPos, newHitObj = rayMarch(lightRayPosition.copy(), newRayVec, scene.objects+scene.lights)

                        if not newRayHitPos: # didnt hit a light
                            continue

                        hit_num += 1
                        objHitColor = newHitObj.color
                        objHitEmit = newHitObj.emit

                    if hit_num == 0: # didnt hit a single light source

                        if self.checkInIllumination(scene, rayHitPos.copy() + normalVec*0.1):
                            pixelColor = Vec3(denoiseColor[0], denoiseColor[1], denoiseColor[2])

                    else:
                        pixelColor = obj.color.multiply_vec(objHitColor * objHitEmit / 255 * (hit_num/brightnessMultiplier))



            pixelColor = fix_color(pixelColor)
            if pixelColor.vec != (0,0,0):
                if pixelColor == denoiseColor:
                    surface.set_at((x, y_batch), denoiseColor)
                    continue

                originalPixelColor = surface.get_at((x, y_batch-1))
                og_pixelColorVec = Vec3(originalPixelColor[0], originalPixelColor[1], originalPixelColor[2])

                if og_pixelColorVec.mag != 0 and og_pixelColorVec.vec != denoiseColor:
                    surface.set_at((x, y_batch), ((pixelColor*(1/rerenderNum) + og_pixelColorVec*((rerenderNum-1)/rerenderNum))).vec)
                else:
                    surface.set_at((x, y_batch), (pixelColor).vec)




    # this uses normal rasterization techniques
    def renderSceneBatch(self, surface, scene, y_batch):
        for x in range(1280):
            pixelColor = Vec3(255,255,255)
            pixelPos = Vec3(ScreenSizeCenter[0] - x, ScreenSizeCenter[1] - y_batch, 0)

            lightRayVec = (pixelPos - self.focal_pos).normalise()
            lightRayPosition = self.centerPos + lightRayVec.copy()

            for rayMarchStep in range(200):

                distanceToObjects = [obj.get_SDF(lightRayPosition) for obj in scene.objects]

                distance = min(distanceToObjects)
                distanceIndex = distanceToObjects.index(distance)
                obj = scene.objects[distanceIndex]

                if distance <= 0.0001 or rayMarchStep == 199:
                    pixelColor = Vec3(0,0,0)
                    for lightPosition in scene.lights:
                        lightToObjVec = (lightPosition.pos - lightRayPosition).normalise()

                        normalVector = obj.get_normal(lightRayPosition)
                        reflectVector = (normalVector * 2 * (lightToObjVec.dot(normalVector)) - lightToObjVec).normalise()
                        reflectVector = reflectVector.clamp()

                        diffuseLighting = (normalVector.dot(lightToObjVec))
                        specularHighlight = reflectVector.dot(lightRayVec) ** 34

                        diffuseComponent = obj.color * diffuseLighting
                        specularComponent = obj.color * specularHighlight
                        ambientComponent = obj.color * 0.2

                        pixelColor += (diffuseComponent + specularComponent + ambientComponent)

                    break

                elif distance > 100000:
                    if lightRayVec.y < scene.plane:
                        y_mag = -(self.centerPos.y-scene.plane)/lightRayVec.y
                        hit_z = lightRayVec.z * y_mag
                        hit_x = lightRayVec.x * y_mag
                        floorPosition = Vec3(hit_x, scene.plane, hit_z)

                        if hit_z-20000 > 0:

                            fog = max(min(1 - (hit_z-20000)/10000,1.0),0.0)
                        else:
                            fog = 1.0

                        if (hit_x//200)%2 == (hit_z//200)%2:
                            baseColor = Vec3(0,0,0) * fog
                        else:
                            baseColor = Vec3(255,255,255) * fog

                        pixelColor = baseColor

                        for lightPosition in scene.lights:
                            lightRayVec = -(floorPosition-lightPosition.pos).normalise()
                            foundLight = False
                            for i in range(100):
                                minDistance = min([obj.get_SDF(floorPosition) for obj in scene.objects])
                                if minDistance < 0.0001:
                                    pixelColor = baseColor * 0.1
                                    break

                                if minDistance > 10000:
                                    pixelColor = baseColor
                                    foundLight = True
                                    break

                                floorPosition += lightRayVec * minDistance

                            if foundLight:
                                break

                    break

                lightRayPosition += lightRayVec * distance

            pixelColor = fix_color(pixelColor)


            surface.set_at((x, y_batch), pixelColor.vec)

    def renderBatch(self, surface, obj,  y_batch):

        lightPosition = Vec3(600, -600, 600)
        for x in range(1280):
            pixelColor = (255,255,255)


            pixelPos = Vec3(ScreenSizeCenter[0]-x, ScreenSizeCenter[1]-y_batch, 0)

            lightRayVec = (pixelPos - self.focal_pos).normalise()
            lightRayPosition = self.centerPos + lightRayVec.copy()

            for rayMarchStep in range(50):

                distance = obj.get_SDF(lightRayPosition)

                if distance > 10000:
                    break

                elif distance <= 0:
                    lightToObjVec = (lightPosition.pos - lightRayPosition).normalise()

                    normalVector = -obj.get_normal(lightRayPosition)
                    reflectVector = (normalVector * 2 * (lightToObjVec.dot(normalVector)) - lightToObjVec).normalise()
                    reflectVector = reflectVector.clamp()

                    diffuseLighting = (normalVector.dot(lightToObjVec))
                    specularHighlight = reflectVector.dot(lightRayVec)**34

                    diffuseComponent = obj.color * diffuseLighting
                    specularComponent = obj.color * specularHighlight

                    pixelColor = fix_color((diffuseComponent + specularComponent).vec)
                    break

                lightRayPosition += lightRayVec*distance

            surface.set_at((x,y_batch), pixelColor)

