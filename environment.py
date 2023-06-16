import actr
import os
# import self_module as selfModule
import json
import headless_simulation as moonlander
import self_module

actr.reset()

timeToStep = 0

modelName = 'prediction-base'
socThreshold = 0.3
modelPath = None
if modelPath is not None:
    actr.load_act_r_model(modelPath)
else:
    # modelPath = os.getcwd() + os.sep + 'cognitive_model.lisp'
    modelPath = os.getcwd() + os.sep + 'cognitive_model.lisp'
    actr.load_act_r_model(modelPath)

ship = None
shipWidth = 30
shipHeight = 30
levelName = None

screen = None
window = None

simTime = 0
environment = None


# color table (as used by the cognitive model)
# purple stochastic disturbance
# red strong disturbance
# orange medium disturbancce
# yellow light disturbance
# green spaceship
# black level elements: lines = border, blocks = obstacles


def updateEnvironment():
    environment.step()


actr.add_command("update-environment", updateEnvironment)


def saveDM(modelName):
    return
    # print(actr.dm())


actr.add_command("saveDM", saveDM)


def setControlInput(controlInput):
    moonlander.control_input = controlInput


actr.add_command('set-control-input', setControlInput)


class Environment:
    def __init__(self):
        pass

    def start(self):
        level_path = 'levels' + os.sep + 'level_3.json'
        moonlander.startSimulation(level_path)
        # trigger the event once act-r starts
        actr.schedule_event_relative(0, "update-environment", time_in_ms=True)

    def step(self):
        stepSize = 10  # in ms
        moonlander.stepSimulation(stepSize)
        self.onEnvironmentData(moonlander.renderMap['ship'], moonlander.renderMap['segments'],
                               moonlander.renderMap['obstacles'], moonlander.renderMap['distortions'])  #
        sim_info = {
            "start_position": {
                "x": moonlander.startX,
                "y": moonlander.startY
            },
            "position": {
                "x": moonlander.shipX,
                "y": moonlander.shipY
            },
            "crash_occurred": moonlander.collisionOccurred
        }
        if moonlander.collisionOccurred:
            print('collision !!!!!!!!!!!!!!!!')
        # self.onSIMToSCLData(sim_info)
        actr.call_command('sim-to-scl', modelName, sim_info)
        actr.schedule_event_relative(stepSize, "update-environment", time_in_ms=True)

    def onEnvironmentData(self, ship, segments, obstacles, driftMarkers):
        # todo here seems to be a bug that objects get the wrong y coordinate

        # this function is called whenever data from headless simulation is received and encoded
        # this contains only visible objects, only used to feed the visicon
        # convert all positions to screen relative positions
        verticalShipPosition = 250
        for i, s in enumerate(segments):
            seg = list(segments[i])
            seg[0] = seg[0]
            seg[1] = seg[1] - ship['y'] + verticalShipPosition
            seg[2] = seg[2]
            seg[3] = seg[3] - ship['y'] + verticalShipPosition
            segments[i] = seg
        for i, s in enumerate(obstacles):
            o = obstacles[i]
            # o['x'] = o['x']
            # o['y'] = o['y'] - ship['y'] + verticalShipPosition
            obstacles[i] = {'radius': o['radius'], 'y': o['y'] - ship['y'] + verticalShipPosition, 'x': o['x']}
        for i, s in enumerate(driftMarkers):
            d = driftMarkers[i]
            d['start_y'] = d['start_y'] - ship['y'] + verticalShipPosition
        ship['y'] = verticalShipPosition  # set ship to center
        self.addToEnvironment(ship, segments, obstacles, driftMarkers)

    def addToEnvironment(self, ship, segments, obstacles, driftMarkers):
        # add to environment adds all visual objects to visicon, hence allows visual module to perceive things
        global window
        actr.clear_exp_window(window)
        for i, segment in enumerate(segments, start=0):
            self.drawLineSegment(segment, window)

        for i, obstacle in enumerate(obstacles, start=0):
            self.drawObstacle(obstacle, window)

        for i, marker in enumerate(driftMarkers, start=0):
            self.drawDriftMarker(marker, window)

        self.drawShip(ship, window)
        actr.add_text_to_exp_window(window, str(actr.mp_time_ms()), x=20, y=40)

    @staticmethod
    def drawLineSegment(segment, window):
        x1 = segment[0]
        x2 = segment[2]
        y1 = segment[1]
        y2 = segment[3]
        # the following distinction doesnt seem to make sense anymore
        # it is a cone line segment when the x values are not equal
        # it was to allow the model to distinguish between cone and normal line
        # without doing any complex comparison
        if x1 != x2:
            actr.add_line_to_exp_window(window, [x1, y1], [x2, y2], color='blue')
        else:
            actr.add_line_to_exp_window(window, [x1, y1], [x2, y2], color='black')

    @staticmethod
    def drawDriftMarker(driftMarker, window):
        y1 = driftMarker['start_y']
        x1 = 10
        x2 = 400
        c = driftMarker['color']
        color = None
        if c == 'rgb(252,0,99)':  # stochastic
            color = 'purple'
        elif c == 'rgb(252,82,3)':  # strong
            color = 'red'
        elif c == 'rgb(252,177,3)':  # medium
            color = 'orange'
        elif c == 'rgb(248,252,3)':  # weak
            color = 'yellow'
        if color is not None:
            actr.add_button_to_exp_window(window, color=color, x=x1, y=y1, width=10,
                                          height=driftMarker['height'])
            actr.add_button_to_exp_window(window, color=color, x=x2, y=y1, width=10,
                                          height=driftMarker['height'])

    @staticmethod
    def drawObstacle(obstacle, window):
        r = obstacle['radius']
        x = obstacle['x'] - r
        y = obstacle['y'] - r
        actr.add_button_to_exp_window(window, color='black', x=x, y=y, width=r * 2, height=r * 2)

    @staticmethod
    def drawShip(ship, window):
        global shipWidth, shipHeight
        y1 = ship["y"] - shipHeight / 2
        x = ship["x"] - shipWidth / 2
        actr.add_button_to_exp_window(window, color='green', x=x, y=y1, width=shipWidth, height=shipHeight)

    def closeSimulation(self):
        global simTime
        print('simulation stopped')
        # self.simDone = True
        # actr.stop()
        # sys.exit()
        chunk = actr.buffer_read('goal')
        actr.schedule_mod_buffer_chunk('goal', ['state', 'reset'], 0, time_in_ms=True)
        simTime = simTime + 7 / 1000
        actr.run_until_time(simTime, False)
        # self.sendDoneMessage()


# def getSocThreshold(name):
#     global socThreshold
#     return socThreshold
#
#
# actr.add_command('get-soc-threshold', getSocThreshold)


def run(threshold=0.3, timeWindow=300, soCBoost=2, time=3000):
    #  time is in seconds, means 3000 equals five minutes
    global window, ship, environment, waitForStepSignal, socThreshold
    socThreshold = threshold
    actr.reset()

    m = actr.call_command("setEnv", modelName)
    print(m)

    actr.call_command("setSoCThreshold", modelName, socThreshold)
    actr.call_command("setTimeWindow", modelName, timeWindow)
    actr.call_command("setSoCBoost", modelName, soCBoost)
    # m.setEnv(environment)
    # selfModule.setEnv(modelName, environment)
    window = actr.open_exp_window("Moonlander", width=800, height=600)

    ship = {"x": 250, "y": 0, "width": 30, "height": 30}  # x,y,radius

    actr.install_device(window)
    environment.start()

    actr.run(time, False)


environment = Environment()


def getDMChunks(formation, disturbance, position):
    # sdp to get activation sdp name activation creation-time last-retrieval-time
    # first get chunks that match search specification
    # e.g. (sdm - slot1 a)
    # second get activation of these chunks
    # e.g. (sdp (a b) :name :activation :creation-time :last-retrieval-time)
    # ['formation', formation, 'disturbance', disturbance, 'position', position, 'result', 'success']
    chunkNames = actr.sdm('formation', formation, 'disturbance', disturbance, 'position', position, 'result', 'success')
    if chunkNames is not None:
        if isinstance(chunkNames, list):
            for name in chunkNames:
                values = actr.sdp(name, ':activation', ':creation-time', ':last-retrieval-time')
                activation = values[0][0]
                creationTime = values[0][1]
                lastRetrievalTime = values[0][2]
                logMessage(None, None, ["time", actr.mp_time_ms(), "event", "dm request success", "parameters",
                                        ['formation', formation, 'disturbance', disturbance, 'position', position,
                                         'result', 'success'], "chunk name", name, "activation", activation,
                                        "creationTime", creationTime, "lastRetrievalTime", lastRetrievalTime])
        else:
            values = actr.sdp(chunkNames, ':activation', ':creation-time', ':last-retrieval-time')
            activation = values[0][0]
            creationTime = values[0][1]
            lastRetrievalTime = values[0][2]
            logMessage(None, None, ["time", actr.mp_time_ms(), "event", "dm request success", "parameters",
                                    ['formation', formation, 'disturbance', disturbance, 'position', position, 'result',
                                     'success'], "activation", activation, "creationTime", creationTime,
                                    "lastRetrievalTime", lastRetrievalTime])
    else:
        logMessage(None, None, ["time", actr.mp_time_ms(), "event", "dm request failed", "parameters",
                                ['formation', formation, 'disturbance', disturbance, 'position', position, 'result',
                                 'success'], "chunk names", chunkNames])


def getModelState(productionName):
    getBufferChunk('situated-state',
                   ["high-level-goal", "disturbance", "situation", "last-situation", "low-level-soc", "high-level-soc",
                    "agent", "agent-x", "agent-y", "position", "strategy1", "strategy2", "strategy3", "crash"],
                   productionName)
    getBufferChunk('goal',
                   ["decision-state", "vision-state", "track-agent", "cone-x", "aoi-y", "obstacle-x", "formation",
                    "boundary-y-1", "boundary-y-2", "soc-threshold", "distance-y", "distance-x", "formation-y",
                    "soc-boost", "soc-time-window", "random-strategy-threshold", "time", "explain-state"],
                   productionName)
    getBufferChunk('imaginal', ["disturbance", "formation", "position", "time", "result"], productionName)


def getBufferChunk(bufferName, slots, productionName):
    chunk = actr.buffer_read(bufferName)
    chunkMap = {}
    if chunk is not None:
        for slotName in slots:
            # because actr.py is horrible
            slotValue = actr.call_command('chunk-slot-value', chunk, slotName)
            chunkMap[slotName] = slotValue
    logMessage(None, None,
               ["time", actr.mp_time_ms(), "event", "buffer read", "called by", productionName, "buffer name",
                bufferName, "chunk", chunkMap])


logData = []


def logMessage(model, something, listOfData):
    message = {}
    for i in range(0, len(listOfData), 2):
        message[listOfData[i]] = listOfData[i + 1]
    logData.append(message)


def saveLog():
    with open('agent.json', 'w', encoding='utf-8') as f:
        json.dump(logData, f, ensure_ascii=False, indent=4)


actr.add_command("logMessage", logMessage)
actr.add_command("saveLog", saveLog)
actr.add_command("getChunks", getDMChunks)
actr.add_command("getModelState", getModelState)
