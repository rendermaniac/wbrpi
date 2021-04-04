import os
import logging
from datetime import datetime
import csv
from collections import defaultdict

import picamera
from matplotlib import pyplot as plt

class Recorder(object):

    HD_FRAMERATE = 30.0

    def __init__(self, datasources):
        self.recording = False
        self.camera_record = False
        
        self.starttime = None
        self.filename = None
        self.notes = None
        self.csv = None

        self.datasources = datasources
        self.reset()

        self.framerate_factor = 1.0
        try:
            self.camera = picamera.PiCamera()
            self.set_camera_hd()
        except:
            self.camera = None
        
        self.todays_date = datetime.now().strftime('%Y_%m_%d')
        self.TELEMETRY_BASE = "/home/pi/"
        self.TELEMETRY_PATH = f"{self.TELEMETRY_BASE}{self.todays_date}/"
        if not os.path.exists(self.TELEMETRY_PATH):
            os.mkdir(self.TELEMETRY_PATH)

        self.csvfile = None
        self.csvhandle = None
        self.apogee_file = None
        self.plot_file = None

        self.plot_fields = ["altitude", "deployed"]

    def reset(self):
        self.apogee_photographed = False
        self.starttime = datetime.now()

    def enable_camera(self, enable):
        self.camera_record = enable
        logging.info(f"Camera recording: {self.camera_record}")

    def set_camera_hd(self):
        if self.camera:
            self.camera.resolution = (1920, 1080)
            self.framerate_factor = 1.0
            self.camera.framerate = self.HD_FRAMERATE
            logging.info(f"Camera set to HD")

    def set_camera_slow_motion(self):
        if self.camera:
            self.camera.resolution = (640, 480)
            self.framerate_factor = 3.0
            self.camera.framerate = self.HD_FRAMERATE * self.framerate_factor
            logging.info(f"Camera set to slow motion")

    def take_apogee_snapshot(self):
        if self.camera and self.camera_record and not self.apogee_photographed:
            self.camera.capture(self.apogee_file, use_video_port=True)
            self.apogee_photographed = True
            logging.info("Taken apogee photo")

    def set_notes(self, notes):
        self.notes = notes
        logging.info(f"Set notes: {self.notes}")

    def start_recording(self):
        self.recording = True
        for datasource in self.datasources:
            datasource.reset()
        self.reset()

        self.filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        # camera has some initialization time
        if self.camera and self.camera_record:
            self.camera.start_recording(f"{self.TELEMETRY_PATH}{self.filename}.h264")
            self.apogee_file = f"{self.TELEMETRY_PATH}{self.filename}.jpg"

        fieldnames = ["time", "duration", "duration_remapped"]
        for datasource in self.datasources:
            fieldnames += datasource.fields

        self.csvfile = f"{self.TELEMETRY_PATH}{self.filename}.csv"
        
        self.csvhandle = open(f"{self.TELEMETRY_PATH}{self.filename}.csv", "w", newline="")
        self.csv = csv.DictWriter(self.csvhandle, fieldnames=fieldnames)
        self.csv.writeheader()

        if self.notes:
            notes = open(f"{self.TELEMETRY_PATH}{self.filename}.txt", "w")
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

            for datasource in self.datasources:
                rowdata.update(datasource.as_dict())

            if self.csv and not self.csvhandle.closed:
                self.csv.writerow(rowdata)
                self.csvhandle.flush()
    
    def plot(self, fig, outfile, clear=True):
        if self.filename:
            plotdata = csv.DictReader(open(self.csvfile, "r", newline=""))
            
            if clear:
                fig.clear()
            
            columns = defaultdict(list)
            for row in plotdata:
                for key, value in row.items():
                    columns[key].append(float(value))

            for key, value in columns.items():
                max_x = 0
                max_y = 0
                if key in self.plot_fields:
                    plt.plot(columns["duration"], value, label=key)

                    for index, y in enumerate(value):
                        max_y = max(max_y, y)
                        if y == max_y:
                            max_x = columns["duration"][index]

                if key == "altitude":
                    plt.annotate(str(max_y), xy=(max_x, max_y))

            fig.savefig(outfile)

            logging.info(f"Generated plot {outfile}")

    def stop_recording(self):
        
        self.recording = False

        if self.csvhandle:
            self.csvhandle.close()

        if self.camera and self.camera_record:
            if self.camera.recording:
                self.camera.stop_recording()

        self.plot_file = f"{self.TELEMETRY_PATH}{self.filename}.png"
        self.plot_file_accumulated = f"{self.TELEMETRY_PATH}/{self.todays_date}.png"

        self.plot(plt.figure(0), self.plot_file)
        self.plot(plt.figure(1), self.plot_file_accumulated, clear=False)

        self.starttime = None
        self.filename = None

        