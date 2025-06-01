#!/usr/bin/env python
'''
Created on Apr 4, 2012

@author: lanquarden

Updated for Python 3.x
'''
import sys
import argparse
import socket
import driver # Assuming you have a driver.py file with a Driver class
import os # Import os module for path manipulation
import csv # Import the csv module
from datetime import datetime # Import datetime for unique filenames

if __name__ == '__main__':
    pass

# Configure the argument parser
parser = argparse.ArgumentParser(description = 'Python client to connect to the TORCS SCRC server.')

parser.add_argument('--host', action='store', dest='host_ip', default='localhost',
                    help='Host IP address (default: localhost)')
parser.add_argument('--port', action='store', type=int, dest='host_port', default=3001,
                    help='Host port number (default: 3001)')
parser.add_argument('--id', action='store', dest='id', default='SCR',
                    help='Bot ID (default: SCR)')
parser.add_argument('--maxEpisodes', action='store', dest='max_episodes', type=int, default=1,
                    help='Maximum number of learning episodes (default: 1)')
parser.add_argument('--maxSteps', action='store', dest='max_steps', type=int, default=0,
                    help='Maximum number of steps (default: 0)')
parser.add_argument('--track', action='store', dest='track', default=None,
                    help='Name of the track')
parser.add_argument('--stage', action='store', dest='stage', type=int, default=3,
                    help='Stage (0 - Warm-Up, 1 - Qualifying, 2 - Race, 3 - Unknown)')
# --- Add argument for data collection mode ---
parser.add_argument('--collectData', action='store_true', dest='collect_data', default=False,
                    help='Enable data collection mode')
parser.add_argument('--dataDir', action='store', dest='data_dir', default='collected_data',
                    help='Directory to save collected data (default: collected_data)')

arguments = parser.parse_args()

# Print summary
print('Connecting to server host ip:', arguments.host_ip, '@ port:', arguments.host_port)
print('Bot ID:', arguments.id)
print('Maximum episodes:', arguments.max_episodes)
print('Maximum steps:', arguments.max_steps)
print('Track:', arguments.track)
print('Stage:', arguments.stage)
print('Data Collection Mode:', arguments.collect_data)
if arguments.collect_data:
    print('Data Directory:', arguments.data_dir)
print('*********************************************')

# Create the data directory if it doesn't exist
if arguments.collect_data and not os.path.exists(arguments.data_dir):
    os.makedirs(arguments.data_dir)
    print(f"Created data directory: {arguments.data_dir}")


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as msg:
    print('Could not make a socket.')
    sys.exit(-1)

# one second timeout
sock.settimeout(1.0)

shutdownClient = False
curEpisode = 0

# You might want to make verbose an argument later, or control it here
verbose = True

# Ensure the driver.py file exists and has a Driver class
try:
    # Pass the data collection flag and directory to the driver
    d = driver.Driver(arguments.stage, collect_data=arguments.collect_data)
except NameError:
    print("Error: The 'driver.py' file or the 'Driver' class was not found.")
    print("Please make sure you have a 'driver.py' file in the same directory")
    print("with a 'Driver' class that has the required methods.")
    sys.exit(-1)


while not shutdownClient:
    curEpisode += 1 # Increment episode counter at the start of the loop

    # --- Data Collection: File Handling for Each Race ---
    data_file = None
    csv_writer = None
    if arguments.collect_data:
        # Generate a unique filename for each race
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use track name and episode number in the filename
        track_name_for_file = arguments.track if arguments.track else "unknown_track"
        filename = f"race_{track_name_for_file}_episode{curEpisode}_{timestamp}.csv"
        filepath = os.path.join(arguments.data_dir, filename)

        try:
            # Open the CSV file for writing for this race
            data_file = open(filepath, 'w', newline='') # newline='' is important for csv module
            csv_writer = csv.writer(data_file)
            print(f"Opened data file for writing: {filepath}")

            # --- Define and Write CSV Header ---
            # You need to list all the sensor and control parameters you want to save.
            # Make sure this list matches the order you write data in driver.py
            header = [
                'speedX', 'speedY', 'speedZ', 'rpm', 'fuel', 'damage', 'sensor_gear',
                'racePos', 'distFromStart', 'distRaced', 'curLapTime', 'lastLapTime',
                'trackPos', 'angle', 'z',
                # Flatten list sensors into multiple columns
                ] + [f'track_{i}' for i in range(19)] + \
                [f'opponents_{i}' for i in range(36)] + \
                [f'wheelSpinVel_{i}' for i in range(4)] + \
                ['accel', 'brake', 'steer', 'control_gear', 'clutch', 'focus', 'meta']

            csv_writer.writerow(header) # Write the header row
            # --- End Define and Write CSV Header ---


        except IOError as e:
            print(f"Error opening data file {filepath}: {e}")
            # Decide if you want to continue without saving or exit
            arguments.collect_data = False # Disable data collection if file can't be opened


    # --- End Data Collection: File Handling ---


    # --- Race Identification Loop ---
    while True:
        print('Sending id to server: ', arguments.id)
        # In Python 3, strings need to be encoded to bytes before sending
        # Pass the csv_writer to the driver's init method if it needs to write header/init data
        # (Though for behavioral cloning, init data isn't usually part of the state)
        buf_to_send = (arguments.id + d.init()).encode()
        print('Sending init string to server:', buf_to_send) # Print the bytes being sent

        try:
            # Send data as bytes
            sock.sendto(buf_to_send, (arguments.host_ip, arguments.host_port))
        except socket.error as msg:
            print("Failed to send data...Exiting...")
            # Ensure file is closed before exiting on error
            if data_file:
                data_file.close()
            sys.exit(-1)

        buf = None # Initialize buf before the try block
        try:
            # Receive data as bytes
            buf_bytes, addr = sock.recvfrom(1000)
            # Decode bytes to a string for processing
            buf = buf_bytes.decode()
        except socket.error as msg:
            # Check if it's a timeout error specifically
            if isinstance(msg, socket.timeout):
                print("Timeout: didn't get response from server during identification...")
            else:
                print(f"Socket error during receive during identification: {msg}")
                # Consider if other socket errors should be fatal
                pass


        if buf is not None and buf.find('***identified***') >= 0:
            print('Received: ', buf)
            break # Exit identification loop
        elif buf is None:
            # If buf is None due to timeout, continue the loop to resend id
            continue
        else:
            # Handle unexpected responses before identification if necessary
            print("Received unexpected response during identification:", buf)
            # You might want to add logic here to decide whether to retry or exit
            pass
    # --- End Race Identification Loop ---

    currentStep = 0

    # --- Main Race Simulation Step Loop ---
    while True:
        # wait for an answer from server (sensor data)
        buf = None
        try:
            # Receive data as bytes
            buf_bytes, addr = sock.recvfrom(1000)
            # Decode bytes to a string for processing
            buf = buf_bytes.decode()
        except socket.error as msg:
            # Check if it's a timeout error specifically
            if isinstance(msg, socket.timeout):
                # print("Timeout: didn't get response from server during race step...")
                pass # Continue loop, try receiving again
            else:
                print(f"Socket error during receive during race step: {msg}")
                # Consider if other socket errors should be fatal
                # Ensure file is closed before exiting on error
                if data_file:
                    data_file.close()
                sys.exit(-1)


        # Check for shutdown or restart messages
        if buf is not None and buf.find('***shutdown***') >= 0:
            print('Received: ', buf)
            d.onShutDown() # Call driver shutdown method
            shutdownClient = True # Set flag to exit main episode loop
            print('Client Shutdown')
            break # Exit the inner step loop (this race)

        if buf is not None and buf.find('***restart***') >= 0:
            print('Received: ', buf)
            d.onRestart() # Call driver restart method
            print('Client Restart')
            break # Exit the inner step loop (this race), will start a new episode


        # --- Process Sensor Data and Get Control Command ---
        buf_to_send = None # Initialize buf_to_send
        if buf is not None: # Only process if a non-None buffer was received (not a timeout)
            currentStep += 1

            # Call the driver's drive method with the sensor data
            # Pass the csv_writer and currentStep to the drive method if in data collection mode
            if arguments.collect_data and csv_writer:
                buf_to_send_str = d.drive(buf, csv_writer=csv_writer, current_step=currentStep)
            else:
                # Standard driving mode (using driver's AI)
                buf_to_send_str = d.drive(buf)

            # Ensure the return value from drive is a string and encode it
            if buf_to_send_str is not None: # Check if drive returned a valid string
                buf_to_send = buf_to_send_str.encode()


        # --- Send Control Command ---
        # Only send data if buf_to_send was generated (i.e., valid sensor data received)
        if buf_to_send is not None:
            if verbose:
                print('Sending: ', buf_to_send)

            try:
                sock.sendto(buf_to_send, (arguments.host_ip, arguments.host_port))
            except socket.error as msg:
                print("Failed to send data...Exiting...")
                # Ensure file is closed before exiting on error
                if data_file:
                    data_file.close()
                sys.exit(-1)

        # Check max steps condition *after* processing the current step
        if arguments.max_steps > 0 and currentStep >= arguments.max_steps:
            print(f"Maximum steps ({arguments.max_steps}) reached for this episode.")
            # Send a meta command to stop? Or let the server handle the end of race?
            # Often reaching max steps means the episode ends, the server might send shutdown or restart
            break # Exit the inner step loop


    # --- End Race Simulation Step Loop ---

    # --- Data Collection: Close File at End of Race ---
    if data_file:
        data_file.close()
        print(f"Closed data file: {filepath}")
    # --- End Data Collection: Close File ---


    # Check if max episodes reached *after* handling the end of the current episode
    # This check is now done at the start of the loop, combined with incrementing curEpisode
    if curEpisode >= arguments.max_episodes:
        shutdownClient = True # Ensure this flag is set to exit the main episode loop

print("Client shutting down completely.")
sock.close()
