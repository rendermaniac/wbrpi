import os
import logging
from datetime import datetime
import csv

import picamera
from matplotlib import pyplot as plt

class Recorder(object):

    HD_FRAMERATE = 30.0

    def __init__(self, sensor, parachute):
        self.recording = False
        self.camera_record = False
        
        self.starttime = None
        self.filename = None
        self.notes = None
        self.csv = None

        self.sensor = sensor
        self.parachute = parachute

        self.reset()

        self.camera = picamera.PiCamera()
        self.framerate_factor = 1.0
        self.set_camera_hd()
        
        telemetry_dir = datetime.now().strftime('%Y_%m_%d')
        os.mkdir(telemetry_dir)
        self.TELEMETRY_PATH = f"/home/pi/{telemetry_dir}/"
        self.csvfile = None
        self.apogee_file = None
        self.plot_file = None

    def reset(self):
        self.altitudes = []
        self.parachute_deploys = []
        self.apogee_photographed = False
        self.starttime = datetime.now()

    def enable_camera(self, enable):
        self.camera_record = enable
        logging.info(f"Camera recording: {self.camera_record}")

    def set_camera_hd(self):
        self.camera.resolution = (1920, 1080)
        self.framerate_factor = 1.0
        self.camera.framerate = self.HD_FRAMERATE
        logging.info(f"Camera set to HD")

    def set_camera_slow_motion(self):
        self.camera.resolution = (640, 480)
        self.framerate_factor = 3.0
        self.camera.framerate = self.HD_FRAMERATE * self.framerate_factor
        logging.info(f"Camera set to slow motion")

    def take_apogee_snapshot(self):
        if self.camera_record and not self.apogee_photographed:
            self.camera.capture(self.apogee_file, use_video_port=True)
            self.apogee_photographed = True
            logging.info("Taken apogee photo")

    def set_notes(self, notes):
        self.notes = notes
        logging.info(f"Set notes: {self.notes}")

    def start_recording(self):
        self.recording = True
        self.sensor.reset()
        self.reset()

        self.filename = datetime.now().strftime("%Y_%m_%d_%H_%M")

        # camera has some initialization time
        if self.camera_record:
            self.camera.start_recording(f"{self.TELEMETRY_PATH}{self.filename}.h264")
            self.apogee_file = f"{self.TELEMETRY_PATH}{self.filename}.jpg"

        self.csvfile = open(f"{self.TELEMETRY_PATH}{self.filename}.csv", "w", newline="")
        
        fieldnames = ["time", "duration", "duration_remapped"]
        fieldnames += self.sensor.fields
        fieldnames += self.parachute.fields

        self.csv = csv.DictWriter(self.csvfile, fieldnames=fieldnames)
        self.csv.writeheader()

        if self.notes:
            notes = open(f"{self.TELEMETRY_PATH}{self.filename}.notes", "w")
            notes.write(f"{self.notes}\n")
            notes.close()

        logging.info(f"Started recording")

    def record_data(self):
        
        if self.recording:

            rowdata = {}
            now = datetime.now()
            rowdata["time"] = datetime.timestamp(now)

            duration = (now - self.starttime).total_seconds()
            rowdata["duration"] = duration
            rowdata["duration_remapped"] = duration * self.framerate_factor

            rowdata.update(self.sensor.as_dict())
            rowdata.update(self.parachute.as_dict())

            if self.csv and not self.csvfile.closed:
                self.csv.writerow(rowdata)
                self.csvfile.flush()

            # for preview plot data
            self.altitudes.append(self.sensor.altitude)
            self.parachute_deploys.append(self.parachute.deployed)
    
    def plot(self):
        if self.filename:
            self.plot_file = f"{self.TELEMETRY_PATH}{self.filename}.png"
            plt.plot(self.altitudes, label="Altitude")
            plt.plot(self.parachute_deploys, label="Parachute Deploy")
            plt.title("Pi High Rockets")
            plt.savefig(self.plot_file)

    def stop_recording(self):
        
        self.recording = False

        if self.csvfile:
            self.csvfile.close()

        if self.camera_record:
            if self.camera.recording:
                self.camera.stop_recording()

        self.starttime = None

        self.plot()

        