import random

import pygame
from Camera import Camera
from objects import *
from Scene import Scene
import time

WHITE = Vec3(255, 255, 255)
BLACK = Vec3(0, 0, 0)
RED = Vec3(255, 0, 0)
SKYBLUE = Vec3(135, 206, 235)

# initialize pygame
pygame.init()
screen_size = (1280, 720)

screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Static Ray Tracer")

clock = pygame.time.Clock()

surface_size = (1280, 720)

surface = pygame.Surface(surface_size)

running = True

y_batch = 719

def make_three_model(color, pos, size):
    capsule_a = Capsule(Vec3(0,-1,0), Vec3(1,-1,0),0.2, Vec3(0,0,0))
    capsule_b = Capsule(Vec3(0,0,0), Vec3(1,0,0),0.2, Vec3(0,0,0))
    capsule_c = Capsule(Vec3(0,1,0), Vec3(1,1,0),0.2, Vec3(0,0,0))
    capsule_d = Capsule(Vec3(0,-1,0), Vec3(0,1,0),0.2, Vec3(0,0,0))


    # combinedObject1 = MergedObjects(capsule_a, capsule_b, pos, size, Vec3(255,0,0))
    combinedObject1 = MergedObjects(capsule_a, capsule_b, Vec3(0,0,0), 1, Vec3(255,0,0))
    # combinedObject2 = MergedObjects(capsule_c, capsule_d, pos, size, Vec3(0,255,0))
    combinedObject2 = MergedObjects(capsule_c, capsule_d, Vec3(0,0,0), 1, Vec3(0,255,0))
    finalCombinedObject = MergedObjects(combinedObject1, combinedObject2, pos, size, color)
    return finalCombinedObject

def make_A_model(color, pos, size):
    capsule_a = Capsule(Vec3(0,1,0), Vec3(0.5,-1,0),0.2, Vec3(0,0,0))
    capsule_b = Capsule(Vec3(0,1,0), Vec3(-0.5,-1,0),0.2, Vec3(0,0,0))
    capsule_c = Capsule(Vec3(-0.35,-0.2,0), Vec3(0.35,-0.2,0),0.2, Vec3(0,0,0))

    combinedObject1 = MergedObjects(capsule_a, capsule_b, Vec3(0,0,0), 1, Vec3(255,0,0))
    finalCombinedObject = MergedObjects(combinedObject1, capsule_c, pos, size, color)

    return finalCombinedObject

def parseFile(text):
    length = len(text)
    textObjects = []
    currTextBlock = ""

    for letter_index in range(length):
        letter = text[letter_index]

        if letter == "{":
            currTextBlock = ""

        elif letter == "}":
            textObjects.append(currTextBlock.strip())

        else:
            currTextBlock += letter

    attributeDictList = []
    for object_text in textObjects:
        attributes = object_text.split(";")
        attributeDict = {}

        for attribute in attributes:
            if attribute == "":
                continue

            attribute = attribute.strip()
            attributePair = attribute.split(":")
            attributeDict[attributePair[0].strip().lower()] = attributePair[1].strip().lower()

        attributeDictList.append(attributeDict)

    return attributeDictList

CameraPosition = Vec3(0,600, 0)
quickRender = False
bounceDepth = 2

def errorHandleVariables(dict, variable, baseCase):
    if variable in dict:
        value = dict[variable]

        # vector
        if value[0] == "(":
            vectorNumArray = value[1:-1].split(",")
            return Vec3(float(vectorNumArray[0]), float(vectorNumArray[1]), float(vectorNumArray[2]))

        else:
            if variable == "type":
                return value

            if value == "true":
                return True
            elif value == "false":
                return False

            if "." in value:
                return float(value)
            return int(value)
    else:
        return baseCase

def createExitStatement(statement, condition):
    if condition:
        print(statement)
        input()
        exit()

def initialiseSceneFromFile():
    f = open("scene_init.txt")
    file_text = f.read()
    f.close()

    ObjectArrayDict = parseFile(file_text)
    objectArray = []
    lightArray = []
    ambientLighting = Vec3(0,0,0)

    for scene_object in ObjectArrayDict:
        objectType = errorHandleVariables(scene_object, "type" ,None)

        if objectType == "settings":
            global quickRender
            global bounceDepth

            ambientLighting = errorHandleVariables(scene_object, "ambient_light", Vec3(0,0,0))
            quickRender = errorHandleVariables(scene_object, "quick_render", False)
            bounceDepth = errorHandleVariables(scene_object, "bounce_depth", 2)

            continue

        pos1 = errorHandleVariables(scene_object, "pos", None)

        createExitStatement("ERROR: ATTRIBUTE 'pos' MUST BE DEFINED", pos1 == None)

        if objectType == "camera":
            if "pos" in scene_object:
                global CameraPosition
                CameraPosition = pos1
            continue


        pos2 = errorHandleVariables(scene_object, "pos2", None)

        size = errorHandleVariables(scene_object, "size", 20)
        color = errorHandleVariables(scene_object, "color", Vec3(255,255,255))

        createExitStatement("ERROR: ATTRIBUTE 'color' SHOULD BE VECTOR IN RANGE (0-255)", (color.x/255) * (color.y/255) * (color.z/255) > 1)

        radiance = errorHandleVariables(scene_object, "radiance", 0)
        reflectivity = errorHandleVariables(scene_object, "reflectivity", 0)
        refractivity = errorHandleVariables(scene_object, "refractivity", 1)

        print(pos1, pos2, size, color, radiance, reflectivity, refractivity)

        object = None
        if objectType == "sphere":
            object = Sphere(pos1, size, color, radiance, reflectivity, refractivity)

        elif objectType == "capsule":
            createExitStatement("ERROR: CAPSULE OBJECT MUST HAVE 'pos2' ATTRIBUTE", pos2 == None)

            object = Capsule(pos1, pos2,size, color, radiance, reflectivity, refractivity)

        elif objectType == "box":
            createExitStatement("ERROR: BOX OBJECT MUST HAVE vec3 'size' ATTRIBUTE",type(size) != Vec3)

            object = Box(pos1, Vec3(0,0,0), size, color, radiance, reflectivity, refractivity)

        elif objectType == "plane":
            createExitStatement("ERROR: PLANE OBJECT MUST HAVE int 'pos' ATTRIBUTE", type(pos1) != int)

            object = Plane(pos1, color, radiance, reflectivity)

        if object.emit > 0:
            lightArray.append(object)
        else:
            objectArray.append(object)

    print(objectArray, lightArray)

    return Scene(objectArray,
                 lightArray,
                 ambientLighting)












camera = Camera(CameraPosition)

# mainScene = Scene([Sphere(Vec3(700,400,1600), 300, Vec3(255,0,0))],
#                   [Sphere(Vec3(-5400,600,1200), 4000, Vec3(255,255,255),1)],
#                   )

mainScene = initialiseSceneFromFile()

rerenderNum = 1


denoiseColor = (123,231, 92)
denoiseColorVec = Vec3(123/255,231/255, 92/255).normalise()



def addNoise(surface, noiseLevel):
    width, height = surface.get_size()
    noiseAmount = int(noiseLevel * width * height)

    for i in range(noiseAmount):
        random_x = random.randint(0,width)
        random_y = random.randint(0, height)
        surface.set_at((random_x, random_y), (0,0,0))

    return surface

# denoise attempt that did not work
def denoise(surface):
    denoiseDepth = 1
    width, height = surface.get_size()


    def inBound(x, y):
        return x >= 0 and x < width and y >= 0 and y < height


    for i in range(denoiseDepth):
        tempSurface = pygame.Surface((width, height), pygame.SRCALPHA)
        for pixel_x in range(width):
            for pixel_y in range(height):
                pixelColor = surface.get_at((pixel_x, pixel_y))

                pixelColorVec = Vec3(pixelColor[0]/255, pixelColor[1]/255, pixelColor[2]/255).normalise()


                if abs(denoiseColorVec.dot(pixelColorVec)) > 0.95:
                    newPixelcolor = [0,0,0]
                    samplePixelNum = 0

                    for x_offset in range(-1, 2):
                        for y_offset in range(-1,2):
                            if x_offset == 0 and y_offset == 0:
                                continue

                            newPixelPos = (pixel_x+x_offset, pixel_y + y_offset)
                            if not inBound(newPixelPos[0], newPixelPos[1]):
                                continue
                            tempPixelColor = surface.get_at((newPixelPos[0], newPixelPos[1]))
                            tempPixelcolorVec = Vec3(tempPixelColor[0]/255, tempPixelColor[1]/255, tempPixelColor[2]/255).normalise()

                            if abs(tempPixelcolorVec.dot(denoiseColorVec)) > 0.95:
                                continue

                            newPixelcolor[0] += tempPixelColor[0]
                            newPixelcolor[1] += tempPixelColor[1]
                            newPixelcolor[2] += tempPixelColor[2]
                            samplePixelNum += 1

                    if samplePixelNum == 0:
                        tempSurface.set_at((pixel_x, pixel_y), (0,0,0))
                        continue



                    finalPixelColor = (newPixelcolor[0]/samplePixelNum, newPixelcolor[1]/samplePixelNum, newPixelcolor[2]/samplePixelNum)

                    tempSurface.set_at((pixel_x, pixel_y), finalPixelColor)
        surface.blit(tempSurface, (0,0))

    return surface

# another denoise attempt that did not work
def denoise2(surface):
    width, height = surface.get_size()

    def inBound(x, y):
        return x >= 0 and x < width and y >= 0 and y < height

    tempSurface = pygame.Surface((width, height), pygame.SRCALPHA)

    for pixel_x in range(width):
        for pixel_y in range(height):
            pixelColor = surface.get_at((pixel_x, pixel_y))


            if sum(pixelColor[:3]) > 40:
                continue

            samplePixelNum = 0
            surroundingPixelsColor = [0,0,0]



            for x_offset in range(-1,2):
                for y_offset in range(-1,2):
                    if x_offset == 0 and y_offset == 0:
                        continue

                    surrounding_x = pixel_x + x_offset
                    surrounding_y = pixel_y + y_offset

                    if inBound(surrounding_x, surrounding_y):
                        surroundingPixelColor = surface.get_at((surrounding_x, surrounding_y))

                        if sum(surroundingPixelColor[:3]) == 0:
                            continue

                        surroundingPixelsColor[0] += surroundingPixelColor[0]
                        surroundingPixelsColor[1] += surroundingPixelColor[1]
                        surroundingPixelsColor[2] += surroundingPixelColor[2]
                        samplePixelNum += 1

            if samplePixelNum >= 5:

                surroundingPixelsColor[0] /= samplePixelNum
                surroundingPixelsColor[1] /= samplePixelNum
                surroundingPixelsColor[2] /= samplePixelNum

                tempSurface.set_at((pixel_x, pixel_y), surroundingPixelsColor)

    surface.blit(tempSurface, (0,0))

    return surface







# denoise and noise attempt
# this is not important towards the ray tracing
randomImage = pygame.transform.scale(pygame.image.load("rayTracingThing4.PNG"), (1280,720))
addNoise(randomImage, 0.1)



while running:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if keys[pygame.K_ESCAPE]:
        running = False

    start = time.time()
    if quickRender:
        camera.quickRenderSceneBatch(surface, mainScene, y_batch)
    else:
        camera.rayTraceRenderSceneBatch2(surface, mainScene, y_batch, bounceDepth, rerenderNum)
    end = time.time()

    print(f"batch {y_batch} : {end - start}")

    if y_batch > 1:
        y_batch -= 1

        if quickRender:
            y_batch -= 2

    else:
        y_batch = 719
        rerenderNum += 1
        print(f"Rerender Iteration: {rerenderNum}")



    screen.fill(BLACK.vec)

    screen.blit(surface, (0,0))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()