'''
Created on Apr 5, 2012

@author: lanquarden

Updated for Python 3.x
'''
import msgParser

class CarState(object):
    '''
    Class that hold all the car state variables
    '''

    def __init__(self):
        '''Constructor'''
        # Assuming msgParser.py is updated for Python 3
        self.parser = msgParser.MsgParser()
        self.sensors = None # Raw dictionary from parser
        # Individual sensor values (initialized to None)
        self.angle = None
        self.curLapTime = None
        self.damage = None
        self.distFromStart = None
        self.distRaced = None
        self.focus = None # This is a list of distances for rangefinders
        self.fuel = None
        self.gear = None
        self.lastLapTime = None
        self.opponents = None # This is a list of distances to opponents
        self.racePos = None
        self.rpm = None
        self.speedX = None
        self.speedY = None
        self.speedZ = None
        self.track = None # This is a list of distances for track edge sensors
        self.trackPos = None
        self.wheelSpinVel = None # This is a list of wheel spin velocities
        self.z = None # Z coordinate (altitude)

    def setFromMsg(self, str_sensors):
        '''Parse the incoming sensor string and populate state variables'''
        # Assuming msgParser.parse is updated for Python 3
        self.sensors = self.parser.parse(str_sensors)

        # Check if parsing was successful before setting individual values
        if self.sensors is not None:
            self.setAngleD()
            self.setCurLapTimeD()
            self.setDamageD()
            self.setDistFromStartD()
            self.setDistRacedD()
            self.setFocusD()
            self.setFuelD()
            self.setGearD()
            self.setLastLapTimeD()
            self.setOpponentsD()
            self.setRacePosD()
            self.setRpmD()
            self.setSpeedXD()
            self.setSpeedYD()
            self.setSpeedZD()
            self.setTrackD()
            self.setTrackPosD()
            self.setWheelSpinVelD()
            self.setZD()
        else:
            print("Warning: Failed to parse sensor message.") # Added a warning if parsing fails


    # The toMsg method seems unnecessary as sensor data comes *from* the server, not sent *to* it
    # This method appears to reverse the parsing, which isn't typically needed for client -> server.
    # Keeping it for completeness but noting its likely non-use case.
    def toMsg(self):
        '''
        Build an UDP message from current state variables (unusual for sensor data)
        This method is likely not needed for a typical client sending control commands.
        '''
        self.sensors = {}

        # Populating the dictionary from stored state values
        # Note: The structure here assumes the stored attributes are lists, matching the parse output structure
        self.sensors['angle'] = [self.angle] if self.angle is not None else None
        self.sensors['curLapTime'] = [self.curLapTime] if self.curLapTime is not None else None
        self.sensors['damage'] = [self.damage] if self.damage is not None else None
        self.sensors['distFromStart'] = [self.distFromStart] if self.distFromStart is not None else None
        self.sensors['distRaced'] = [self.distRaced] if self.distRaced is not None else None
        self.sensors['focus'] = self.focus if self.focus is not None else None # focus is a list
        self.sensors['fuel'] = [self.fuel] if self.fuel is not None else None
        self.sensors['gear'] = [self.gear] if self.gear is not None else None
        self.sensors['lastLapTime'] = [self.lastLapTime] if self.lastLapTime is not None else None
        self.sensors['opponents'] = self.opponents if self.opponents is not None else None # opponents is a list
        self.sensors['racePos'] = [self.racePos] if self.racePos is not None else None
        self.sensors['rpm'] = [self.rpm] if self.rpm is not None else None
        self.sensors['speedX'] = [self.speedX] if self.speedX is not None else None
        self.sensors['speedY'] = [self.speedY] if self.speedY is not None else None
        self.sensors['speedZ'] = [self.speedZ] if self.speedZ is not None else None
        self.sensors['track'] = self.track if self.track is not None else None # track is a list
        self.sensors['trackPos'] = [self.trackPos] if self.trackPos is not None else None
        self.sensors['wheelSpinVel'] = self.wheelSpinVel if self.wheelSpinVel is not None else None # wheelSpinVel is a list
        self.sensors['z'] = [self.z] if self.z is not None else None


        # Assuming msgParser.stringify is updated for Python 3
        return self.parser.stringify(self.sensors)

    # Helper methods to safely get data from the parsed sensors dictionary

    def getFloatD(self, name):
        '''Safely get a float value from the sensors dictionary'''
        try:
            val = self.sensors.get(name) # Use .get() to avoid KeyError if key is missing
        except AttributeError:
             # Handle case where self.sensors is None or not a dictionary
             val = None

        if val is not None and isinstance(val, list) and len(val) > 0 and val[0] is not None:
            try:
                return float(val[0])
            except (ValueError, TypeError):
                print(f"Warning: Could not convert sensor '{name}' value '{val[0]}' to float.")
                return None # Return None if conversion fails
        return None # Return None if key is missing, value is None, or list is empty/malformed


    def getFloatListD(self, name):
        '''Safely get a list of float values from the sensors dictionary'''
        try:
            val = self.sensors.get(name) # Use .get() to avoid KeyError
        except AttributeError:
            # Handle case where self.sensors is None or not a dictionary
            val = None

        if val is not None and isinstance(val, list):
             l = []
             for v in val:
                 try:
                     l.append(float(v))
                 except (ValueError, TypeError):
                     print(f"Warning: Could not convert list element '{v}' for sensor '{name}' to float.")
                     # Decide whether to append None, skip, or raise error
                     l.append(None) # Append None for problematic values
             return l if l else None # Return the list, or None if it's empty
        return None # Return None if key is missing or value is not a list

    def getIntD(self, name):
        '''Safely get an int value from the sensors dictionary'''
        try:
            val = self.sensors.get(name) # Use .get() to avoid KeyError
        except AttributeError:
             # Handle case where self.sensors is None or not a dictionary
             val = None


        if val is not None and isinstance(val, list) and len(val) > 0 and val[0] is not None:
            try:
                return int(val[0])
            except (ValueError, TypeError):
                 print(f"Warning: Could not convert sensor '{name}' value '{val[0]}' to int.")
                 return None # Return None if conversion fails
        return None # Return None if key is missing, value is None, or list is empty/malformed


    # Setter and Getter methods for each sensor value
    # Setters allow setting the state manually if needed (less common for incoming data)
    # Getters retrieve the stored state values

    # Added type hints for clarity (optional but good practice in modern Python)

    def setAngle(self, angle: float):
        self.angle = angle

    def setAngleD(self):
        self.angle = self.getFloatD('angle')

    def getAngle(self) -> float | None:
        return self.angle

    def setCurLapTime(self, curLapTime: float):
        self.curLapTime = curLapTime

    def setCurLapTimeD(self):
        self.curLapTime = self.getFloatD('curLapTime')

    def getCurLapTime(self) -> float | None:
        return self.curLapTime

    def setDamage(self, damage: float):
        self.damage = damage

    def setDamageD(self):
        self.damage = self.getFloatD('damage')

    def getDamage(self) -> float | None:
        return self.damage

    def setDistFromStart(self, distFromStart: float):
        self.distFromStart = distFromStart

    def setDistFromStartD(self):
        self.distFromStart = self.getFloatD('distFromStart')

    def getDistFromStart(self) -> float | None:
        return self.distFromStart

    def setDistRaced(self, distRaced: float):
        self.distRaced = distRaced

    def setDistRacedD(self):
        self.distRaced = self.getFloatD('distRaced')

    def getDistRaced(self) -> float | None:
        return self.distRaced

    def setFocus(self, focus: list[float]):
        self.focus = focus

    def setFocusD(self):
        self.focus = self.getFloatListD('focus')

    def getFocus(self) -> list[float] | None:
        return self.focus

    def setFuel(self, fuel: float):
        self.fuel = fuel

    def setFuelD(self):
        self.fuel = self.getFloatD('fuel')

    def getFuel(self) -> float | None:
        return self.fuel

    def setGear(self, gear: int):
        self.gear = gear

    def setGearD(self):
        self.gear = self.getIntD('gear')

    def getGear(self) -> int | None:
        return self.gear

    def setLastLapTime(self, lastLapTime: float):
        self.lastLapTime = lastLapTime

    def setLastLapTimeD(self):
        self.lastLapTime = self.getFloatD('lastLapTime')

    def getLastLapTime(self) -> float | None:
        return self.lastLapTime

    def setOpponents(self, opponents: list[float]):
        self.opponents = opponents

    def setOpponentsD(self):
        self.opponents = self.getFloatListD('opponents')

    def getOpponents(self) -> list[float] | None:
        return self.opponents

    def setRacePos(self, racePos: int):
        self.racePos = racePos

    def setRacePosD(self):
        self.racePos = self.getIntD('racePos')

    def getRacePos(self) -> int | None:
        return self.racePos

    def setRpm(self, rpm: float):
        self.rpm = rpm

    def setRpmD(self):
        self.rpm = self.getFloatD('rpm')

    def getRpm(self) -> float | None:
        return self.rpm

    def setSpeedX(self, speedX: float):
        self.speedX = speedX

    def setSpeedXD(self):
        self.speedX = self.getFloatD('speedX')

    def getSpeedX(self) -> float | None:
        return self.speedX

    def setSpeedY(self, speedY: float):
        self.speedY = speedY

    def setSpeedYD(self):
        self.speedY = self.getFloatD('speedY')

    def getSpeedY(self) -> float | None:
        return self.speedY

    def setSpeedZ(self, speedZ: float):
        self.speedZ = speedZ

    def setSpeedZD(self):
        self.speedZ = self.getFloatD('speedZ')

    def getSpeedZ(self) -> float | None:
        return self.speedZ

    def setTrack(self, track: list[float]):
        self.track = track

    def setTrackD(self):
        self.track = self.getFloatListD('track')

    def getTrack(self) -> list[float] | None:
        return self.track

    def setTrackPos(self, trackPos: float):
        self.trackPos = trackPos

    def setTrackPosD(self):
        self.trackPos = self.getFloatD('trackPos')

    def getTrackPos(self) -> float | None:
        return self.trackPos

    def setWheelSpinVel(self, wheelSpinVel: list[float]):
        self.wheelSpinVel = wheelSpinVel

    def setWheelSpinVelD(self):
        self.wheelSpinVel = self.getFloatListD('wheelSpinVel')

    def getWheelSpinVel(self) -> list[float] | None:
        return self.wheelSpinVel

    def setZ(self, z: float):
        self.z = z

    def setZD(self):
        self.z = self.getFloatD('z')

    def getZ(self) -> float | None:
        return self.z