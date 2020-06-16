import os
import sys
import json
import socket
import pickle
import base64
import cv2
import imutils
import face_recognition
sys.path.append(os.path.join("..", "lib"))
import socket_utils


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
POSITIONS_FILE = os.path.join(os.path.dirname(__file__), "positions.json")


class AgentPi:
    '''Agent Pi Console App

    To be installed on Agent Pi on the car for communication with Master Pi
    '''

    def __init__(self, conf_file):
        '''Constructor'''

        with open(conf_file, "r") as f:
            self._conf = json.load(f)

        with open(POSITIONS_FILE, "r") as f:
            self._positions = json.load(f)


    def console(self):
        '''Console-based menu application'''

        while True:
            print("Select an operation:")
            print("1. Unlock this car")
            print("2. Return this car")
            print("q. Leave the system")
            cmd = input("> ")
            print()

            if cmd in ["1", "2"]:
                if self._submenu(int(cmd)):
                    break
            elif cmd == "q":
                print("Thanks")
                break
            else:
                print("ERROR: Invalid input")
            print()


    def _submenu(self, cmd):
        '''Submenu after selecing a command

        Args:
            cmd (str) : command

        Returns:
            (bool) True on success, or False on failure
        '''

        while True:
            print("{} by:".format("Unlock" if cmd == 1 else "Return"))
            print("1. Username and passowrd")
            print("2. Facial recognition")
            print("p. Previous menu")
            method = input("> ")
            print()

            if method in ["1", "2"]:
                if method == "1":
                    payload = {
                        "username": input("Username: "),
                        "password": input("Password: "),
                        "state": "in-use" if cmd == 1 else "returned",
                        "id": self._conf["agent"]["id"]
                    }
                else:
                    photo = input("Photo filename: ")
                    encodings = self._extractFaceFeatures(photo)
                    payload = {
                        "encodings": [x.tolist() for x in encodings] if encodings is not None else None,
                        "state": "in-use" if cmd == 1 else "returned",
                        "id": self._conf["agent"]["id"]
                    }
                print()
                if cmd == 2:
                    position = self._detectPosition()
                    payload.update(position)
                resp = self._execute(payload)
                if resp["rc"]  == 0:
                    print("Hi {} {},".format(resp["account"]["first_name"], resp["account"]["last_name"]))
                    print("Successfully {} this car".format("unlocked" if cmd == 1 else "returned"))
                    return True
                else:
                    print("Failed to {} this car".format("unlock" if cmd == 1 else "return"))
            elif method == "p":
                return False
            else:
                print("ERROR: Invalid input")
            print()


    def _extractFaceFeatures(self, photo):
        '''Extract face features for machine learning recognition

        Args:
            photo (str) : filename of the photo uploaded

        Returns:
            (list) encodings of the features
        '''

        try:
            encodings = None
            photo_path = os.path.join(os.path.dirname(__file__), "photo", photo)
            img = cv2.imread(photo_path)
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            rgb = imutils.resize(img, width=240)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
        except Exception:
            pass

        return encodings


    def _detectPosition(self):
        '''Simulating position detection

        User selects a position to demostrate the function of updating location

        Returns:
            (dict) geo position with location, latitude and longitude
        '''

        while True:
            print("Simulate position:")
            for k in self._positions:
                print("{}. {}".format(k, self._positions[k]["location"]))
            pos = input("> ")
            print()

            if pos in ["1", "2", "3"]:
                return self._positions[pos]
            else:
                print("ERROR: Invalid input")
            print()


    def _execute(self, payload):
        '''Execute command via TCP connection to Master Pi

        Args:
            payload (dict): data being transfer to Master Pi

        Returns:
            (dict) result including rc and an account dict
        '''

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self._conf["master"]["host"], self._conf["master"]["port"]))
            socket_utils.sendJson(s, payload)
            resp = socket_utils.recvJson(s)

        return resp


def main():
    '''Entry point of Agent Pi application'''

    ap = AgentPi(CONFIG_FILE)
    ap.console()


if __name__ == "__main__":
    main()
