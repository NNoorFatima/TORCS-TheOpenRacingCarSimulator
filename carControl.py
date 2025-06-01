'''
Created on Apr 5, 2012

@author: lanquarden

Updated for Python 3.x
'''
import msgParser

class CarControl(object):
    '''
    An object holding all the control parameters of the car
    '''
    # TODO range check on set parameters

    def __init__(self, accel = 0.0, brake = 0.0, gear = 1, steer = 0.0, clutch = 0.0, focus = 0, meta = 0):
        '''Constructor'''
        # Assuming msgParser.py is updated for Python 3
        self.parser = msgParser.MsgParser()

        self.actions = None

        self.accel = accel
        self.brake = brake
        self.gear = gear
        self.steer = steer
        self.clutch = clutch
        self.focus = focus
        self.meta = meta

    def toMsg(self):
        self.actions = {}

        # Note: The SCR protocol expects values as strings, which stringify handles
        self.actions['accel'] = [self.accel]
        self.actions['brake'] = [self.brake]
        self.actions['gear'] = [self.gear]
        self.actions['steer'] = [self.steer]
        self.actions['clutch'] = [self.clutch]
        self.actions['focus'] = [self.focus]
        self.actions['meta'] = [self.meta]

        # Assuming msgParser.stringify is updated for Python 3 and handles list inputs
        return self.parser.stringify(self.actions)

    # Setter and Getter methods (standard Python 3 compatible)
    def setAccel(self, accel):
        self.accel = accel

    def getAccel(self):
        return self.accel

    def setBrake(self, brake):
        self.brake = brake

    def getBrake(self):
        return self.brake

    def setGear(self, gear):
        # TODO: Add range check for gear
        self.gear = gear

    def getGear(self):
        return self.gear

    def setSteer(self, steer):
        # TODO: Add range check for steer (-1 to 1 relative to steer_lock)
        self.steer = steer

    def getSteer(self):
        return self.steer

    def setClutch(self, clutch):
        self.clutch = clutch

    def getClutch(self):
        return self.clutch

    def setFocus(self, focus):
         # TODO: Check valid focus values if necessary
         self.focus = focus

    def getFocus(self):
         return self.focus

    def setMeta(self, meta):
        # TODO: Check valid meta values if necessary
        self.meta = meta

    def getMeta(self):
        return self.meta