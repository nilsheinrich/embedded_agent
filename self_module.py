import actr
import os
import numpy as np

from hpbu_compas import Hierarchy, Config


selfModules = {}
#  actr.undefine_module('self')


# self module code

def setEnv(name):
    m = getSelfModule(name)
    m.setEnv(name)


def setTimeWindow(name, data):
    m = getSelfModule(name)
    m.setTimeWindow(data)


def setSoCBoost(name, data):
    m = getSelfModule(name)
    m.setSoCBoost(data)


def setSoCThreshold(name, data):
    m = getSelfModule(name)
    m.setSoCThreshold(data)


def selfModuleBufferQuery(name, buffer, slot, value):
    m = getSelfModule(name)
    return m.query(buffer, slot, value)


def selfModuleBufferRequest(name, buffer, spec):
    m = getSelfModule(name)
    return m.request(buffer, spec)


def selfModuleSetParameter(name, param):
    # currently no parameters are implemented, future parameters: size of action field
    # increase, decrease rate of high level SoC
    # low level SoC
    m = getSelfModule(name)
    return m.setParameter(param)


def selfModuleReset(name):
    m = getSelfModule(name)
    return m.reset()


def selfModuleDelete(name):
    global selfModules
    if name is None:
        return
    if name.lower() in selfModules:
        del selfModules[name.lower()]


def selfModuleCreate(name):
    global selfModules
    selfModules[name.lower()] = SelfModule(name.lower())
    return name


def selfModuleBufferCleared(name, buffer, chunk):
    m = getSelfModule(name)
    return m.onClear(buffer, chunk)


def selfModuleBufferMod(name, buffer, mods):
    m = getSelfModule(name)
    return m.onModification(buffer, mods)


def getSelfModule(name):
    global selfModules
    if name is None:
        return next(iter(selfModules.values()))
    return selfModules[name.lower()]


def selfModuleBufferUpdate(name):
    module = getSelfModule(name)
    return module.updateBuffer()


def simToSCL(name, data):
    module = getSelfModule(name)
    module.onSIMToSCLData(data)

# def getFirstModule():
#     global selfModules
#     return module
#     # return selfModules[selfModules.keys()[0]]


class SelfModule:

    def __init__(self, name):
        self.chunkSlots = ['high-level-goal', 'disturbance', 'situation', 'last-situation',
                           'position',
                           'low-level-soc', 'high-level-soc', 'agent', 'agent-x', 'agent-y',
                           'strategy1',
                           'strategy2', 'strategy3', 'sr1', 'sr2', 'sr3', 'goal-error', 'crash']
        self.situatedStateChunk = self.createEmptyChunk()
        self.chunkNumber = 0
        self.chunkNumberIntention = 0
        self.currentChunkName = None
        self.env = None
        self.goalX = 0
        self.x = 0
        self.startX = 0
        self.startTime = 0
        self.dXPerMs = 0
        self.ySpeedPerMs = 6/10  # 6/1000
        self.updateNeeded = False
        self.name = name
        self.updateEventScheduled = False
        self.chunkExists = False
        self.highLevelSoC = 0
        self.socUpdateTicks = 0
        self.modelName = ""
        self.socThreshold = 0
        self.timeWindow = 0
        self.socBoost = 0
        self.chunkNumberEpisode = 0
        self.actionEpisodes = []
        self.actionEpisodeBufferSize = 5

        # SCL stuff
        self.hierarchy = None
        self.setupSCL()

    def setEnv(self, modelName):
        self.modelName = modelName

    def setSoCThreshold(self, value):
        self.socThreshold = value

    def setSoCBoost(self, value):
        self.socBoost = value

    def setTimeWindow(self, value):
        self.timeWindow = value

    def reset(self):
        self.situatedStateChunk = self.createEmptyChunk()
        self.chunkNumber = 0
        self.currentChunkName = None
        self.chunkNumberIntention = 0
        #self.createAndAddACTRChunk()  this is not the right way because the model (that contains the chunk definition isn't initialized yet)

    def updateSlot(self, slot, value):
        self.situatedStateChunk[slot]['value'] = value
        self.situatedStateChunk[slot]['update'] = True
        self.updateNeeded = True  # ♥

    def updateHLSoC(self):
        chunk = actr.buffer_read('situated-state')
        if chunk is not None:
            hlSoC = actr.call_command('chunk-slot-value', chunk, 'high-level-soc')
            llSoC = self.situatedStateChunk['low-level-soc']['value']
            if llSoC is None or hlSoC is None:
                #  no feedback received yet, can happen...
                #  do nothing...
                print('no low level or high level soc values yet... if you see this often, something went wrong')
                return None
            if llSoC > hlSoC:
                hlSoC = hlSoC + 1/10
                if hlSoC > 1.0:
                    hlSoC = 1.0
                self.updateSlot('high-level-soc', hlSoC)
                self.highLevelSoC = hlSoC
            elif llSoC < hlSoC - 1/10:
                hlSoC = hlSoC - 1/10
                if hlSoC < 0.0:
                    hlSoC = 0.0
                self.updateSlot('high-level-soc', hlSoC)
                self.highLevelSoC = hlSoC
            else:
                self.updateSlot('high-level-soc', hlSoC)
                self.highLevelSoC = hlSoC

    def onExternalInput(self, feedback, soc, crash):
        yPosition = feedback[1]
        xPosition = feedback[0] + 300
        # goalError = self.goalX - xPosition
        self.x = xPosition
        self.updateSlot('agent-x', xPosition)
        self.updateSlot('agent-y', yPosition)
        self.updateSlot('low-level-soc', soc)
        #self.updateSlot('goal-error', self.computeGoalError())
        print(['crash in self', crash])
        if crash or crash == 'True':
            print('update slot')
            self.updateSlot('crash', "True")
        else:
            print('update slot 2')
            self.updateSlot('crash', "False")
        # self.situatedStateChunk['agent-x'] = xPosition
        # self.situatedStateChunk['agent-y'] = yPosition
        # self.situatedStateChunk['low-level-soc'] = soc

        # self.situatedStateChunk['goal-error'] = self.computeGoalError()
        self.updateNeeded = True  # schedule update from external update, lower frequency of updates?
        if not self.updateEventScheduled:
            # this starts the update buffer loop (but only once, hence the flag)
            self.updateEventScheduled = True
            self.updateBuffer()

    def onModification(self, buffer, mods):
        self.onInternalInput(mods)

    def updateBuffer(self):
        # self.socUpdateTicks = self.socUpdateTicks + 1
        # if self.socUpdateTicks > 10:
        #     self.socUpdateTicks = 0
        self.updateHLSoC()
        self.updateChunkInput()
        actr.schedule_event_relative(10, "update-self-module", time_in_ms=True, params=[self.name])

    def onInternalInput(self, elements):
        if isinstance(elements, list):
            for e in elements:
                self.parseRequest(e)
        else:
            self.parseRequest(elements)
        self.updateNeeded = True
        self.updateChunkInput()  # immediately update from internal input

    def parseRequest(self, request):
        operation = request[0]
        slotName = request[1].lower()
        slotValue = request[2]
        if isinstance(slotValue, str):
            slotValue = slotValue.lower()
        # self.situatedStateChunk[slotName] = slotValue
        self.updateSlot(slotName, slotValue)

    def updateGoal(self, elements):
        x = 0
        y = 0
        disturbance = 0
        goalX = 0
        strategy = 'none'
        for e in elements:
            operation = e[0]
            slotName = e[1].lower()
            slotValue = e[2]
            if isinstance(slotValue, str):
                slotValue = slotValue.lower()
            if slotName == 'x':
                x = slotValue
            elif slotName == 'y':
                y = slotValue
            elif slotName == 'disturbance':
                disturbance = slotValue
            elif slotName == 'goal-x':
                goalX = slotValue
            elif slotName == 'type':
                strategy = slotValue

        self.goalX = int(goalX)
        self.startX = self.x
        self.startTime = actr.get_time(True)
        self.dXPerMs = (self.goalX - self.startX) / (200*self.ySpeedPerMs)

        self.chunkNumberIntention = self.chunkNumberIntention + 1
        chunkName = 'action-intention-chunk-{}'.format(self.chunkNumberIntention)
        chunks = actr.define_chunks([chunkName])
        actr.set_chunk_slot_value(chunkName, 'x', x)
        actr.set_chunk_slot_value(chunkName, 'y', y)
        actr.set_chunk_slot_value(chunkName, 'goal-x', goalX)
        actr.set_chunk_slot_value(chunkName, 'disturbance', disturbance)
        actr.set_chunk_slot_value(chunkName, 'type', strategy)
        actr.schedule_set_buffer_chunk('action-intention', chunkName, 0, time_in_ms=True)
        # update last action episode (soc value)
        # self.setActionEpisodeSoC(self.situatedStateChunk['low-level-soc']['value'])

        # add entry into action episode buffer
        # self.addActionEpisode({'x': x, 'y': y, 'goal-x': goalX, 'type': type, 'time': actr.get_time(True), 'soc': -1})
       # actr.call_command("sendSCLData", self.modelName, [x, y, disturbance])
        self.onActionIntention({'target': {'x': x, "y": y}, "compensation bias": disturbance})

    def setParameter(self, param):
        return None

    def request(self, buffer, spec):
        elements = actr.call_command('chunk-spec-slot-spec', spec)
        buffer = buffer.lower()
        if buffer == 'situated-state':
            self.onInternalInput(elements)
        elif buffer == 'action-intention':
            self.updateGoal(elements)

    def query(self, buffer, slot, value):
        buffer = buffer.lower()
        slot = slot.lower()
        value = value.lower()
        if buffer == 'situated-state':
            if slot == 'state':
                if value == 'free':
                    return True
        elif buffer == 'action-intention':
            if slot == 'state':
                if value == 'free':
                    return True
        elif buffer == 'action-episode':
            if slot == 'state':
                if value == 'free':
                    return True
        else:
            actr.print_warning('Unknown state query %s to goal module' % value)
        return True

    def onClear(self, buffer, chunk):
        if buffer.lower() == 'situated-state':
            print("situated state empty again...")
            print(chunk)
            self.chunkExists = False

    def createAndAddACTRChunk(self):
        print('create chunk')
        self.chunkExists = True
        self.chunkNumber = self.chunkNumber + 1
        chunkName = 'situated-state-chunk-{}'.format(self.chunkNumber)
        chunks = actr.define_chunks([chunkName])
        self.currentChunkName = chunkName
        for slot in self.chunkSlots:
            if self.situatedStateChunk[slot] is not None:  # and self.situatedStateChunk[slot] != 'nil'
                actr.set_chunk_slot_value(chunkName, slot, self.situatedStateChunk[slot]['value'])
                self.situatedStateChunk[slot]['update'] = False
        actr.schedule_set_buffer_chunk('situated-state', chunkName, 0, time_in_ms=True, module='self')

    def updateChunkInput(self):
        if self.updateNeeded:
            # self.env.sendSoCMessage(self.highLevelSoC)
            actr.call_command("sendSoCMessage", self.modelName, self.highLevelSoC)
            self.updateNeeded = False
            # chunkName = actr.buffer_chunk('situated-state')
            # actr.call_command('pprint-chunks-plus', [chunkName])
            #
            # chunkName = actr.buffer_chunk('goal')
            # actr.call_command('pprint-chunks-plus', [chunkName])
            #
            # chunkName = actr.buffer_chunk('action-intention')
            # actr.call_command('pprint-chunks-plus', [chunkName])
            if not self.chunkExists:

                # update goal buffer content!
                # this was a previous hack around a communication issue, now
                # these parameters should be set in a production
                # or directly as part of the goal chunk
                # or refactored to be a parameter but some productions use these values
                actr.schedule_mod_buffer_chunk('goal', ['soc-threshold', self.socThreshold,
                                                        'soc-boost', self.socBoost,
                                                        'soc-time-window', self.timeWindow],
                                               0, time_in_ms=True)
                self.createAndAddACTRChunk()
            else:
                mods = []
                for slot in self.chunkSlots:
                    # if self.situatedStateChunk[slot] is not None and self.situatedStateChunk[slot] != 'nil':
                    if self.situatedStateChunk[slot]['update']:
                        value = self.situatedStateChunk[slot]['value']
                        self.situatedStateChunk[slot]['update'] = False
                        mods.append(slot)
                        mods.append(value)
                actr.schedule_mod_buffer_chunk('situated-state', mods, 5, time_in_ms=True, module='self')

    def createEmptyChunk(self):
        chunkMap = {}
        for key in self.chunkSlots:
            chunkMap[key] = {'value': None, 'update': False}
        return chunkMap

    def computeGoalError(self):
        target = self.goalX
        current = self.x
        start = self.startX
        change = self.ySpeedPerMs
        time = actr.get_time(True)
        deltaTime = time - self.startTime
        error = current - (self.dXPerMs*deltaTime + start)
        return error
        # self.situatedStateChunk['goal-error'] = error
        # distance point line

    def setActionEpisodeSoC(self, socValue):
        if len(self.actionEpisodes) > 1:
            latestEpisode = self.actionEpisodes[-1]
            latestEpisode['soc'] = socValue

    def addActionEpisode(self, actionIntention):
        # {'x': x, 'y': y, 'goal-x': goalX, 'type': type, 'time': actr.get_time(True), 'soc': -1}
        self.actionEpisodes.append(actionIntention)  # add new entry
        if len(self.actionEpisodes) > self.actionEpisodeBufferSize:
            self.actionEpisodes.pop(0)  # remove oldest (first) entry
        # build new chunk
        self.chunkNumberEpisode = self.chunkNumberEpisode + 1
        chunkName = 'action-episode-chunk-{}'.format(self.chunkNumberEpisode)
        chunks = actr.define_chunks([chunkName])
        for i in range(0, len(self.actionEpisodes)):
            intention = self.actionEpisodes[i]
            actr.set_chunk_slot_value(chunkName, 'x-{}'.format(i), intention['x'])
            actr.set_chunk_slot_value(chunkName, 'y-{}'.format(i), intention['y'])
            actr.set_chunk_slot_value(chunkName, 'goal-x-{}'.format(i), intention['goal-x'])
            actr.set_chunk_slot_value(chunkName, 'type-{}'.format(i), intention['type'])
            actr.set_chunk_slot_value(chunkName, 'time-{}'.format(i), intention['time'])
            actr.set_chunk_slot_value(chunkName, 'soc-{}'.format(i), intention['soc'])
        actr.schedule_set_buffer_chunk('action-episode', chunkName, 0, time_in_ms=True)

    def onSIMToSCLData(self, sim_observation):
        # there is some weird conversion happening here (python -> lisp -> python
        # i don't know why this happens here.. but all keys look different
        observation = None
        long_range_compensation = {}
        start_position = sim_observation[":START--POSITION"]  # instead of 'start_position'
        position = sim_observation[":POSITION"]
        if "crash_occurred" in sim_observation:
            long_range_compensation.update({
                "Compensation": {
                    "crash": True
                }
            })
            self.hierarchy.set_long_range_projection(long_range_compensation)
        rel_coords = np.array(
            [position[':X'] - start_position[':X'], position[':Y'] - start_position[':Y']])

        observation = {
            "Vision": [rel_coords, 0],
            "MC": rel_coords
        }

        prediction, feedback, soc, max_compensation = self.hierarchy.update(_input=observation, _top_down=None)
        print([prediction, feedback, soc, max_compensation])
        actr.call_command('set-control-input', prediction)
        self.onExternalInput([position[':X'], position[':Y']], soc, sim_observation[':CRASH--OCCURRED'])

    def onActionIntention(self, intention):
        long_range_compensation = {}
        target = intention["target"]
        rel_coords = [target['x'],
                      target['y']]  # target from ccl is a coordinate relative from the ship's position
        goal_error = rel_coords

        if "compensation bias" in intention:
            bias = intention["compensation bias"]

            long_range_compensation.update({
                "Compensation": {
                    "intention": rel_coords,
                    "compensation bias": bias
                }
            })
        else:
            long_range_compensation.update({
                "Compensation": {
                    "intention": rel_coords
                }
            })
        k = self.hierarchy.set_long_range_projection(long_range_compensation)
        print(k)

    def setupSCL(self):
        my_path = os.path.dirname(os.path.abspath(__file__))
        my_path += os.sep + "configs"

        agent_config = Config(my_path, "sensorimotor_hierarchy.json")
        storage = agent_config.read_config_storage()
        agent_config.config_layer_from_storage()
        agent_config.config_parameters_from_storage()

        """
        HPBU SETUP
        """
        #config = agent_config.parameters
        #print(config)
        self.hierarchy = Hierarchy(agent_config)
        my_id = self.hierarchy.my_id
        simulation_running = False
        # layer setup (if required)
        self.hierarchy.get_layer("Vision").gen_primitives()
        self.hierarchy.get_layer("MC").gen_primitives()
        self.hierarchy.get_layer("Compensation").gen_primitives()


actr.add_command("query-self-module", selfModuleBufferQuery)
actr.add_command("request-self-module-buffer", selfModuleBufferRequest)
actr.add_command("create-self-module", selfModuleCreate)
actr.add_command("delete-self-module", selfModuleDelete)
actr.add_command("reset-self-module", selfModuleReset)
actr.add_command("params-self-module", selfModuleSetParameter)
actr.add_command("cleared-self-module", selfModuleBufferCleared)
actr.add_command("update-self-module", selfModuleBufferUpdate)
actr.add_command("buffer-mod-self-module", selfModuleBufferMod)
actr.add_command("getSelfModule", getSelfModule)
actr.add_command("setEnv", setEnv)
actr.add_command("setSoCThreshold", setSoCThreshold)
actr.add_command("setTimeWindow", setTimeWindow)
actr.add_command("setSoCBoost", setSoCBoost)
actr.add_command("sim-to-scl", simToSCL)

# actr.call_command('clear-all')

actr.define_module('self',
                   [['situated-state'], ['action-intention'], ['action-episode']],
                   [
                   ],
                   [['version', '0.1'],
                    ['documentation', 'Simple module shell for providing buffers for the self representation'],
                    ['creation', 'create-self-module'],
                    ['delete', 'delete-self-module'],
                    ['query', 'query-self-module'],
                    ['request', 'request-self-module-buffer'],
                    ['buffer-mod', 'buffer-mod-self-module'],
                    ['reset', 'reset-self-module'],
                    ['params', 'params-self-module'],
                    ['notify-on-clear', 'cleared-self-module']])
