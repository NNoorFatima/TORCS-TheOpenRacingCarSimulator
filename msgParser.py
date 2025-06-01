'''
Created on Apr 5, 2012

@author: lanquarden

Updated for Python 3.x
'''

class MsgParser(object):
    '''
    A parser for received UDP messages and building UDP messages
    '''
    def __init__(self):
        '''Constructor'''
        # In Python 3, object is the base class, so (object) is optional but harmless
        # super().__init__() # If inheriting from a class that needs its __init__ called

    def parse(self, str_sensors):
        '''Return a dictionary with tags and values from the UDP message'''
        sensors = {}

        b_open = str_sensors.find('(')

        while b_open >= 0:
            b_close = str_sensors.find(')', b_open)
            if b_close >= 0:
                substr = str_sensors[b_open + 1: b_close]
                items = substr.split()
                if len(items) < 2:
                    # Updated print statement for Python 3
                    print("Problem parsing substring: ", substr)
                else:
                    value = []
                    for i in range(1,len(items)):
                        value.append(items[i])
                    sensors[items[0]] = value
                b_open = str_sensors.find('(', b_close)
            else:
                # Updated print statement for Python 3
                print("Problem parsing sensor string: ", str_sensors)
                return None

        return sensors

    def stringify(self, dictionary):
        '''Build an UDP message from a dictionary'''
        msg = ''

        # .items() in Python 3 returns a view, which is fine here
        for key, value in dictionary.items():
            # Check if value is not None and if it's a list/iterable with at least one element that's not None
            # The original code checked value[0] != None, assuming value is a list.
            # Let's maintain that assumption or refine if needed.
            if value is not None and isinstance(value, list) and len(value) > 0 and value[0] is not None:
                msg += '(' + key
                for val in value:
                    msg += ' ' + str(val) # Ensure values are strings
                msg += ')'

        return msg