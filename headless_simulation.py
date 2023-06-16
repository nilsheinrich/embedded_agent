import json

import logging

from tkinter import *

""" 
LOGGING
"""
logger = logging.getLogger("SIM")

"""
GLOBALS
"""

# level
segments_max_y = 0
lineSegments = []
obstacles = []
distortions = []
markers = []
inputNoise = []
speed = None
startX = None
startY = None
inputStrength = None
noiseCondition = False
shipLines = [
    [-5, -15, 5, -15],
    [5, -15, 9, -12],
    [9, -12, 9, 0],
    [9, 0, 6, 0],
    [6, 0, 9, 15],
    [9, 15, 3, 4],
    [3, 4, -3, 4],
    [-3, 4, -9, 15],
    [-9, 15, -6, 0],
    [-6, 0, -9, 0],
    [-9, 0, -9, -12],
    [-9, -12, -5, -15]
]

# game state
control_input = 0
currentNoise = None  # object with y and modifier field
noiseIndex = 0
obstacleIndex = 0
segmentsIndex = 0
disturbanceIndex = 0
collisionOccurred = False
testsDisabled = 0

shipX = 0
shipY = 0
fov = 0

simTime = 0

renderMap = {}  # for rendering purposes only


def loadAndParseLevel(levelPath):
    global lineSegments, obstacles, distortions, markers, segments_max_y
    global inputNoise, speed, startX, startY, inputStrength, fov
    with open(levelPath, 'r') as file:
        data = file.read()
        levelJson = json.loads(data)
        lineSegments = prepareSegments(levelJson['segments'])
        segments_max_y = lineSegments[-1][3]
        logger.info("max level y: {}".format(segments_max_y))
        obstacles = levelJson['obstacles']
        distortions = levelJson['distortion']
        markers = levelJson['marker']
        inputNoise = inputNoiseModifier(levelJson['input_noise'])
        speed = levelJson['speed']  # levelJson needs to contain pixels/second
        startX = levelJson['start_x']
        startY = levelJson['start_y']
        inputStrength = levelJson['input_strength']
        fov = levelJson['fov_height']


def prepareSegments(segmentsJson):
    orderedSegmentList = []
    for id in segmentsJson:
        points = segmentsJson[id]  # list of points
        lastPoint = None
        for point in points:
            if lastPoint is not None:
                orderedSegmentList.append((lastPoint["x"], lastPoint["y"], point["x"], point["y"]))
            else:
                lastPoint = point
    orderedSegmentList.sort(key=lambda tup: tup[1])  # sort by y (start of line)
    return orderedSegmentList


def inputNoiseModifier(noiseJson):
    for i, noise in enumerate(noiseJson):
        noiseJson[i]['modifier'] = noise['modifier']  # TODO: add input noise function
    return noiseJson


def startSimulation(levelPath):
    """ Entry for the simulation.
    """
    global simTime, noiseIndex, obstacleIndex, segmentsIndex, disturbanceIndex, shipX, shipY
    simTime = 0
    noiseIndex = 0
    obstacleIndex = 0
    segmentsIndex = 0
    disturbanceIndex = 0
    loadAndParseLevel(levelPath)
    shipX = startX
    shipY = startY


def stepSimulation(deltaTimeInMS):
    """ Update for the simulation.
    """
    global simTime
    simTime = simTime + deltaTimeInMS
    updateGameState(deltaTimeInMS)  #deltaTimeInMS)


def getDisturbance(y):
    global distortions, disturbanceIndex
    if len(distortions) == 0:
        return None
    
    for i, d in enumerate(distortions, start=disturbanceIndex):
        if d['start_y'] < y and y < d['start_y'] + d['height']:
            disturbanceIndex = i
            return d
    return None


def getDriftMarkers(horizon_upper, horizon_lower):
    global distortions
    if len(distortions) == 0:
        return []
    markerList = []
    for i, d in enumerate(distortions):
        if d['color'] is not None:
            # begins before endY and ends after begin
            if d['start_y'] < horizon_lower and d['start_y']+d['height'] > horizon_upper:
                markerList.append(distortions[i])
    return markerList


def getObstacles(startY, endY):
    global obstacles, obstacleIndex
    if len(obstacles) == 0:
        return []
    obstaclesToTest = []
    # very simplified algorithm, not flexible
    obstacleIndex = 0
    for i, o in enumerate(obstacles, start=obstacleIndex):
        if o['y']-o['radius'] > startY and o['y']+o['radius'] < endY:
            obstaclesToTest.append(o)
        elif o['y']+o['radius'] > endY:
            break
    return obstaclesToTest


def getSegments(y1, y2):
    global segmentsIndex, lineSegments
    if len(lineSegments) == 0:
        return None
    segmentsToDraw = []
    newIndex = None
    for i, line in enumerate(lineSegments, segmentsIndex):
        if line[1] <= y2 and line[3] >= y1:  # segment begins before y2 and does not end before y1, fixed always find horizontal lines
            segmentsToDraw.append(line)
            if newIndex is None:
                newIndex = i  # new start point
    segmentsIndex = newIndex
    return segmentsToDraw


def getInputNoise(y):
    global noiseIndex, inputNoise
    if len(inputNoise) == 0:
        return None
    for i, n in enumerate(inputNoise, start=noiseIndex):
        if y > n['y']:
            break
        else:
            noiseIndex = i
    return inputNoise[noiseIndex]


def collisionTestSegments(shipX, shipY, segments):
    for s in segments:
        for l in shipLines:
            x1 = l[0] + shipX
            y1 = l[1] + shipY
            x2 = l[2] + shipX
            y2 = l[3] + shipY
            if lineLineIntersection(s[0], s[1], s[2], s[3], x1, y1, x2, y2):
                return True
    return False


def collisionTestObstacle(shipX, shipY, shipLines, obstacle):
    rSquared = obstacle['radius'] * obstacle['radius']
    x = obstacle['x']
    y = obstacle['y']
    for i, line in enumerate(shipLines):
        cX = line[0] + shipX
        cY = line[1] + shipY
        dX = line[2] + shipX
        dY = line[3] + shipY
        if circleLineCollision(x, y, rSquared, cX, cY, dX, dY):
            return True
    return False


def circleLineCollision(x, y, rSquared, x1, y1, x2, y2):
    xDelta = x2 - x1
    yDelta = y2 - y1

    u = ((x - x1) * xDelta + (y - y1) * yDelta) / (xDelta * xDelta + yDelta * yDelta)

    xP = None
    yP = None
    if u < 0:
        xP = x1
        yP = y1
    elif u > 1:
        xP = x2
        yP = y2
    else:
        xP = x1 + u * xDelta
        yP = y1 + u * yDelta
    distanceSquared = (x - xP) * (x - xP) + (y - yP) * (y - yP)
    return rSquared > distanceSquared


def lineLineIntersection(line1StartX, line1StartY, line1EndX, line1EndY, line2StartX, line2StartY, line2EndX,
                         line2EndY):
    # if the lines intersect, the result contains the x and y of the intersection (treating the lines as infinite)
    # and booleans for whether line segment 1 or line segment 2 contain the point
    result = {
        'x': None,
        'y': None
    }
    denominator = ((line2EndY - line2StartY) * (line1EndX - line1StartX)) - (
                (line2EndX - line2StartX) * (line1EndY - line1StartY))
    if denominator == 0:
        return None

    a = line1StartY - line2StartY
    b = line1StartX - line2StartX
    numerator1 = ((line2EndX - line2StartX) * a) - ((line2EndY - line2StartY) * b)
    numerator2 = ((line1EndX - line1StartX) * a) - ((line1EndY - line1StartY) * b)
    a = numerator1 / denominator
    b = numerator2 / denominator

    # if we cast these lines infinitely in both directions, they intersect here:
    result['x'] = line1StartX + (a * (line1EndX - line1StartX))
    result['y'] = line1StartY + (a * (line1EndY - line1StartY))
    # if line1 is a segment and line2 is infinite, they intersect if:
    if 0 < a < 1 and 0 < b < 1:
        return result
    return None


def resetPosition():
    global shipX, shipY, noiseIndex, obstacleIndex, segmentsIndex, disturbanceIndex
    # reset
    noiseIndex = 0  # reset values
    obstacleIndex = 0
    segmentsIndex = 0
    disturbanceIndex = 0
    # collisionOccurred = False

    # reset position
    segments = getSegments(shipY, shipY)
    segments.sort(key=lambda segment: segment[0])  # sort by x position of segment start
    startX = segments[0][0]  # first element of list = leftmost
    endX = segments[-1][0]  # last element of list = rightmost
    shipX = startX + (endX - startX)/2  # simply place ship between them


def updateGameState(deltaTimeInMS):
    """ Main update logic.
    """ 
    # move ship (apply disturbance, apply input (incl. input noise)), test for collision (obstacles and walls)
    # speed in pixels per seconds
    global shipY, shipX, speed, inputStrength, shipLines, testsDisabled, renderMap, collisionOccurred, control_input

    # reset collision detection at the beginning of the update, so it can be detected after updating the game state
    # collisionOccurred = False

    print(control_input)

    noise = 1.0
    oldY = shipY
    if noiseCondition:
        noise += getInputNoise(shipY)['modifier']
        logger.debug("input noise added: {}".format(noise))
    disturbance = getDisturbance(shipY)
    driftStrength = 0.0
    if disturbance is not None:
        driftStrength = disturbance['strength']
        if disturbance['dir'] == 'toLeft':
            driftStrength *= -1
        logger.debug("disturbance added: {}".format(driftStrength))
    shipY += speed * (deltaTimeInMS/1000)  #  / 1000 * timeInMs

    # apply control (with noise) and disturbance
    # shipX = shipX + ((control_input * inputStrength * noise) / 1000 + driftStrength / 1000) * timeInMs
    driftStrength = 0.0
    print([shipX, ((control_input * inputStrength * noise) + driftStrength) * (deltaTimeInMS/1000)])
    shipX += ((control_input * inputStrength * noise) + driftStrength) * (deltaTimeInMS/1000)
    if control_input != 0:
        # reset control
        control_input = 0

    obstacles = getObstacles(shipY - fov, shipY + fov)
    segments = getSegments(shipY - fov, shipY + fov)

    # collision detection:
    collisionOccurredNow = False
    if testsDisabled <= 0.0:
        collisionOccurred = False
        for o in obstacles:
            if collisionTestObstacle(shipX, shipY, shipLines, o):
                collisionOccurredNow = True
                logger.debug("collision occurred with obstacle at coordinate: {:.0f}/{:.0f}(x/y)".format(shipX,shipY))
                break
        if not collisionOccurred:
            if collisionTestSegments(shipX, shipY, segments):
                collisionOccurredNow = True
                logger.debug("collision occurred with segment at coordinate: {:.0f}/{:.0f}(x/y)".format(shipX,shipY))

    if testsDisabled > 0:
        testsDisabled = testsDisabled - (shipY - oldY)
        print(testsDisabled)
    if collisionOccurredNow:
        print('collision detected')
        #  disable collision checks for at least 200 px after a crash occurred
        collisionOccurred = True
        testsDisabled = 100
        resetPosition()

    driftMarkers = getDriftMarkers(shipY-(1.5*fov), shipY+(1.5*fov))

    # rendering
    # sceneJson = json.dumps({
    #     'segments': segments,
    #     'obstacles': obstacles,
    #     'driftMarkers': driftMarkers,
    #     'ship': {'x': shipX, 'y': shipY}
    # })
    renderMap = {
        'segments': segments,
        'obstacles': obstacles,
        'distortions': driftMarkers,
        'ship': {'x': shipX, 'y': shipY},
        'soc': 0.0
    }
    # only for log
    logger.debug("ship position (x/y): {:.0f}/{:0f}".format(shipX,shipY))

# todo sample data


# tk = Tk()
# window = Canvas(tk, width=600, height=800)
# window.pack()
#
#
# def renderView():
#     updateGameState(20)
#
#     window.create_line(0, 0, 50, 20, fill="#476042", width=3)
#     tk.update_idletasks()
#     tk.update()
#
#
# renderView()
