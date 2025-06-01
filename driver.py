'''
Created on Apr 4, 2012
@author: lanquarden
Updated for Python 3.x with NN model integration for autonomous driving
Includes manual control for data collection.
Corrected sensor extraction and prediction mapping for the NN.
'''

import msgParser
import carState
import carControl
import csv
from pynput import keyboard
import threading
import time
import numpy as np
import torch  # Import PyTorch
import torch.nn as nn  # Import nn
import joblib

# --- Define the MLP model class (same as your training script) ---
class MLP(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(MLP, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.model(x)
# --- End model definition ---

class Driver(object):
    '''
    A driver object for the SCRC
    '''

    def __init__(self, stage: int, collect_data: bool = False):
        '''Constructor'''
        self.WARM_UP = 0
        self.QUALIFYING = 1
        self.RACE = 2
        self.UNKNOWN = 3
        self.stage = stage

        self.parser = msgParser.MsgParser()
        self.state = carState.CarState()
        self.control = carControl.CarControl()

        # Simple AI constants (used for simple AI fallback mode)
        self.steer_lock = 0.785398
        self.max_speed = 100
        self.prev_rpm = None

        # Initialize rangefinder angles (needed for init message)
        self.angles = [0.0] * 19
        for i in range(5):
            self.angles[i] = -90.0 + i * 15.0
            self.angles[18 - i] = 90.0 - i * 15.0
        for i in range(5, 9):
            self.angles[i] = -20.0 + (i-5) * 5.0
            self.angles[18 - i] = 20.0 - (i-5) * 5.0

        self.collect_data = collect_data  # Store the data collection flag

        # --- Load the Trained Model and Scaler if not collecting data ---
        self.nn_model = None
        self.feature_scaler = None
        self.model_filename = 'torcs_mlp_model.pth'  # Changed to PyTorch model name
        self.scaler_filename = 'scaler_multi_output.pkl'
        self.nn_output_names = ['accel', 'brake', 'steer', 'clutch', 'gear']  # Corrected to match the actual outputs.  Removed focus and meta.
        self.num_gear_classes = 7
        self.label_columns = ['accel', 'brake', 'steer', 'clutch', 'gear']  # Corrected label columns

        # Define the list of feature columns (MUST exactly match feature_columns in preprocess_data.py)
        self.feature_columns = [
            'speedX', 'speedY', 'speedZ', 'rpm', 'fuel', 'damage', 'sensor_gear',
            'racePos', 'distFromStart', 'distRaced', 'curLapTime', 'lastLapTime',
            'trackPos', 'angle', 'z',
        ] + [f'track_{i}' for i in range(19)] + \
            [f'opponents_{i}' for i in range(36)] + \
            [f'wheelSpinVel_{i}' for i in range(4)]


        if not self.collect_data:
            try:
                print(f"Driver: Loading trained PyTorch model from file '{self.model_filename}'...")
                # Instantiate the model with the correct input and output dimensions
                #  Crucially, input_dim must match the number of features.
                #  output_dim must match the number of target variables.
                self.nn_model = MLP(input_dim=len(self.feature_columns), output_dim=len(self.label_columns))
                # Load the model's state_dict (the trained weights)
                self.nn_model.load_state_dict(torch.load(self.model_filename))
                self.nn_model.eval()  # Set the model to evaluation mode
                print("Driver: Model loaded successfully.")

                print(f"Driver: Loading scaler from '{self.scaler_filename}'...")
                self.feature_scaler = joblib.load(self.scaler_filename)
                print("Driver: Scaler loaded successfully.")

            except (FileNotFoundError, ImportError, Exception) as e:
                print(f"Driver: Error loading model or scaler: {e}")
                print("Driver: Falling back to simple AI driver.")
                self.nn_model = None
                self.feature_scaler = None

        # --- Manual Control Attributes (for data collection mode) ---
        self.manual_accel = 0.0
        self.manual_brake = 0.0
        self.manual_steer = 0.0
        self.manual_gear = 1
        self.last_gear_change_time = 0
        self.key_states = {
            keyboard.Key.up: False,
            keyboard.Key.down: False,
            keyboard.Key.left: False,
            keyboard.Key.right: False,
            keyboard.KeyCode(char='a'): False,
            keyboard.KeyCode(char='z'): False,
            keyboard.KeyCode(char='r'): False,
        }
        self.listener = None

        if self.collect_data:
            print("Driver: Data Collection Mode: Setting up keyboard listener (Arrow keys for control, 'a' for gear down, 'z' for gear up, 'r' for reverse).")
            self.listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release)
            self.listener.start()

    def determine_gear_rule_based(self):
        """
        Determines gear based on rules (RPM, speed).
        TORCS gears: -1 (Reverse), 0 (Neutral), 1, 2, ..., 6.
        Updates self.control.gear directly.
        """
        rpm = self.state.getRpm()
        current_sensor_gear = self.state.getGear()
        speed = self.state.getSpeedX()

        target_gear = self.control.getGear()
        if current_sensor_gear is not None:
            target_gear = current_sensor_gear

        if self.prev_rpm is None and rpm is not None:
            self.prev_rpm = rpm
        
        if rpm is not None and speed is not None and self.prev_rpm is not None:
            rpm_increasing = (rpm > self.prev_rpm)

            rpm_upshift = 8000
            rpm_downshift = 2500
            
            if target_gear == 0 and speed < 5 and self.control.getAccel() > 0.2:
                target_gear = 1
            elif self.control.getBrake() > 0.8 and speed < 1 and target_gear >= 0 :
                if speed < -0.5 :
                    target_gear = -1
                elif target_gear > 0 :
                    target_gear = 0

            elif rpm > rpm_upshift and 1 <= target_gear < 6:
                target_gear += 1
            elif rpm < rpm_downshift and target_gear > 1:
                target_gear -= 1
            
            if speed < 2 and target_gear > 0 and self.control.getAccel() < 0.1:
                target_gear = 0

        if target_gear >= 1:
            target_gear = max(1, min(6, target_gear))
        elif target_gear == 0:
            target_gear = 0
        else:
            target_gear = -1
        
        self.control.setGear(int(target_gear))

    def on_key_press(self, key):
        """Callback for when a key is pressed.  Handles character keys case-insensitively."""
        if hasattr(key, 'char'):
            char_pressed = key.char.lower()
            if char_pressed in ['a', 'z', 'r']:
                key_code_for_state = keyboard.KeyCode(char=char_pressed)
                if key_code_for_state in self.key_states:
                    self.key_states[key_code_for_state] = True
                self.handle_gear_shift(char_pressed)
                return
        if key in self.key_states:
            self.key_states[key] = True
            self.update_manual_controls()

    def on_key_release(self, key):
        """Callback for when a key is released. Handles character keys case-insensitively."""
        if hasattr(key, 'char'):
            char_released = key.char.lower()
            key_code_for_state = keyboard.KeyCode(char=char_released)
            if key_code_for_state in self.key_states:
                self.key_states[key_code_for_state] = False
            return
        if key in self.key_states:
            self.key_states[key] = False
            self.update_manual_controls()

    def update_manual_controls(self):
        """Update manual control values based on current key states (Accel, Brake, Steer)."""
        if self.key_states[keyboard.Key.up]:
            self.manual_accel = 1.0
            self.manual_brake = 0.0
        elif self.key_states[keyboard.Key.down]:
            self.manual_accel = 0.0
            self.manual_brake = 1.0
        else:
            self.manual_accel = 0.0
            self.manual_brake = 0.0

        if self.key_states[keyboard.Key.left] and not self.key_states[keyboard.Key.right]:
            self.manual_steer = 1.0
        elif self.key_states[keyboard.Key.right] and not self.key_states[keyboard.Key.left]:
            self.manual_steer = -1.0
        else:
            self.manual_steer = 0.0


    def handle_gear_shift(self, char: str):
        """Handle gear shifts based on 'a', 'z', and 'r' key characters."""
        current_time = time.time()
        if current_time - self.last_gear_change_time < 0.2 and char in ['a', 'z']:
            return

        old_gear = self.manual_gear
        new_gear = old_gear

        if char == 'a':
            new_gear -= 1
            new_gear = max(0, new_gear)
            self.last_gear_change_time = current_time
        elif char == 'z':
            new_gear += 1
            new_gear = min(6, new_gear)
            self.last_gear_change_time = current_time
        elif char == 'r':
            new_gear = -1
            self.last_gear_change_time = current_time

        if new_gear != old_gear:
            self.manual_gear = new_gear


    def init(self) -> str:
        '''Return init string with rangefinder angles'''
        return self.parser.stringify({'init': self.angles})

    def drive(self, msg: str, csv_writer=None, current_step=None) -> str:
        '''
        Process incoming sensor message, decide control, and optionally save data/predict control.
        This is where your AI logic (or manual input) will go.
        '''
        self.state.setFromMsg(msg)

        if self.collect_data and csv_writer is not None and current_step is not None:
            gear_to_send = self.manual_gear
            self.control.setAccel(self.manual_accel)
            self.control.setBrake(self.manual_brake)
            self.control.setSteer(self.manual_steer)
            self.control.setGear(gear_to_send)

            sensor_data_row = [
                self.state.getSpeedX(), self.state.getSpeedY(), self.state.getSpeedZ(),
                self.state.getRpm(), self.state.getFuel(), self.state.getDamage(),
                self.state.getGear(),
                self.state.getRacePos(), self.state.getDistFromStart(),
                self.state.getDistRaced(), self.state.getCurLapTime(), self.state.getLastLapTime(),
                self.state.getTrackPos(), self.state.getAngle(), self.state.getZ(),
            ]
            track_sensors = self.state.getTrack()
            opponent_sensors = self.state.getOpponents()
            wheel_spin_vel = self.state.getWheelSpinVel()
            sensor_data_row.extend(track_sensors if track_sensors is not None else [None] * 19)
            sensor_data_row.extend(opponent_sensors if opponent_sensors is not None else [None] * 36)
            sensor_data_row.extend(wheel_spin_vel if wheel_spin_vel is not None else [None] * 4)

            control_data_row = [
                self.control.getAccel(), self.control.getBrake(), self.control.getSteer(),
                self.control.getClutch(),
                # self.control.getFocus(),  Removed focus and meta
                # self.control.getMeta()
            ]

            full_data_row = sensor_data_row + control_data_row
            try:
                csv_writer.writerow(full_data_row)
            except Exception as e:
                print(f"Error writing data row for step {current_step}: {e}")

        elif self.nn_model is not None and self.feature_scaler is not None:
            sensor_values_for_prediction = []

            for col in self.feature_columns:
                if col.startswith('track_'):
                    track_idx = int(col.split('_')[1])
                    track_sensors = self.state.getTrack()
                    sensor_values_for_prediction.append(track_sensors[track_idx] if track_sensors and len(track_sensors) > track_idx else 0.0)
                elif col.startswith('opponents_'):
                    opp_idx = int(col.split('_')[1])
                    opponent_sensors = self.state.getOpponents()
                    sensor_values_for_prediction.append(opponent_sensors[opp_idx] if opponent_sensors and len(opponent_sensors) > opp_idx else 200.0)
                elif col.startswith('wheelSpinVel_'):
                    wheel_idx = int(col.split('_')[1])
                    wheel_spin_vel = self.state.getWheelSpinVel()
                    sensor_values_for_prediction.append(wheel_spin_vel[wheel_idx] if wheel_spin_vel and len(wheel_spin_vel) > wheel_idx else 0.0)
                else:
                    getter_map = {
                        'speedX': self.state.getSpeedX, 'speedY': self.state.getSpeedY, 'speedZ': self.state.getSpeedZ,
                        'rpm': self.state.getRpm, 'fuel': self.state.getFuel, 'damage': self.state.getDamage,
                        'sensor_gear': self.state.getGear, 'racePos': self.state.getRacePos,
                        'distFromStart': self.state.getDistFromStart, 'distRaced': self.state.getDistRaced,
                        'curLapTime': self.state.getCurLapTime, 'lastLapTime': self.state.getLastLapTime,
                        'trackPos': self.state.getTrackPos, 'angle': self.state.getAngle, 'z': self.state.getZ,
                    }
                    getter = getter_map.get(col)
                    value = getter()
                    sensor_values_for_prediction.append(value if value is not None else 0.0)

            sensor_data_np = np.array(sensor_values_for_prediction).astype(np.float32)
            sensor_data_reshaped = sensor_data_np.reshape(1, -1)
            scaled_sensor_data = self.feature_scaler.transform(sensor_data_reshaped)

            # Convert the scaled data to a PyTorch tensor
            sensor_data_torch = torch.from_numpy(scaled_sensor_data).float()  # crucial .float()

            # Make the prediction using the PyTorch model
            self.nn_model.eval()  # Set to evaluation mode
            with torch.no_grad():  # Disable gradient calculation
                predictions_torch = self.nn_model(sensor_data_torch)  # Get predictions
            predictions_np = predictions_torch.numpy()  # convert to numpy

            # Map the predictions to the car control outputs.  predictions_np[0] because we have a batch size of 1.
            accel_command = np.clip(predictions_np[0][self.nn_output_names.index('accel')], 0.0, 1.0)
            brake_command = np.clip(predictions_np[0][self.nn_output_names.index('brake')], 0.0, 1.0)
            steer_command = np.clip(predictions_np[0][self.nn_output_names.index('steer')], -1.0, 1.0)
            clutch_command = np.clip(predictions_np[0][self.nn_output_names.index('clutch')], 0.0, 1.0)
            # gear_command = int(round(np.clip(predictions_np[0][self.nn_output_names.index('gear')], 0, 6))) # No gear output from NN
            
            self.control.setAccel(accel_command)
            self.control.setBrake(brake_command)
            self.control.setSteer(steer_command)
            self.control.setClutch(clutch_command)
            # self.control.setGear(gear_command) #  Use rule based gear.

            # Determine gear using rule-based logic
            self.determine_gear_rule_based() # This will call self.control.setGear()

        elif not self.collect_data:
            print("Driver: Model or scaler not loaded in __init__, falling back to simple AI driver.")
            self.steer()
            self.gear()
            self.speed()

        new_rpm = self.state.getRpm()
        if new_rpm is not None:
            self.prev_rpm = new_rpm
        
        return self.control.toMsg()

    def onShutDown(self):
        '''
        Called when the server sends a ***shutdown*** message.
        Use this to perform any cleanup, including stopping the keyboard listener.
        '''
        print("Driver: Shutting down.")
        if self.listener:
            self.listener.stop()
            print("Driver: Keyboard listener stopped.")
        pass

    def onRestart(self):
        '''
        Called when the server sends a ***restart*** message.
        Use this to reset any internal state for a new race.
        '''
        print("Driver: Restarting.")
        self.state = carState.CarState()
        self.control = carControl.CarControl()

        if self.collect_data and self.listener:
            self.manual_accel = 0.0
            self.manual_brake = 0.0
            self.manual_steer = 0.0
            self.manual_gear = 1
            self.last_gear_change_time = time.time()
            for key in self.key_states:
                self.key_states[key] = False
            self.update_manual_controls()

        self.prev_rpm = None
        pass

    def steer(self):
        angle = self.state.getAngle()
        dist = self.state.getTrackPos()
        if angle is not None and dist is not None:
            steer_command = (angle - dist * 0.5) / self.steer_lock
            self.control.setSteer(np.clip(steer_command, -1.0, 1.0))
        else:
            self.control.setSteer(0.0)

    def gear(self):
        rpm = self.state.getRpm()
        gear = self.state.getGear()
        speed = self.state.getSpeedX()

        if rpm is not None and gear is not None and speed is not None:
            up = False
            if self.prev_rpm is not None:
                if (self.prev_rpm - rpm) < 0:
                    up = True

            if gear == 0 and speed < 10.0 and self.control.getAccel() > 0.1:
                gear = 1
            elif up and rpm > 7000 and 1 <= gear < 6:
                gear += 1
            elif not up and rpm < 3000 and gear > 1:
                gear -= 1
            elif speed < 1.0 and self.control.getAccel() <= 0.1 and gear > 0:
                gear = 0

            gear = max(0, min(6, gear))
            self.control.setGear(gear)

    def speed(self):
        speed = self.state.getSpeedX()
        accel = self.control.getAccel()

        if speed is not None:
            if speed < self.max_speed:
                accel += 0.1
                if accel > 1.0:
                    accel = 1.0
            else:
                accel -= 0.1
                if accel < 0.0:
                    accel = 0.0
            self.control.setAccel(accel)
