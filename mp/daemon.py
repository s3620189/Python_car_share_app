import os
import sys
import socket
import pickle
from datetime import datetime
from datetime import timedelta
import numpy
import face_recognition
from werkzeug.security import check_password_hash
from masterpi.restutils import RestUtils
sys.path.append(os.path.join("..", "lib"))
import socket_utils


DAEMON_ADDR = ("localhost", 5050)


class Daemon:
    '''Master Pi Daemon

    To serve the connection from Agent Pi and to process the its request
    '''

    def __init__(self, addr=None):
        '''Constructor'''

        if addr is None:
            self._addr = DAEMON_ADDR
        else:
            self._addr = addr

    def run(self):
        '''Start running the daemon'''

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self._addr)
            s.listen()

            print("Listening on {}...".format(self._addr))
            while True:
                print("Waiting for Agent...")
                conn, addr = s.accept()
                with conn:
                    print("Accepted connection from {}...".format(addr))

                    data = socket_utils.recvJson(conn)
                    resp = self._updateDetails(data)
                    socket_utils.sendJson(conn, resp)

    def _updateDetails(self, data):
        '''Update booking details

        Args:
            data (dict) : data of request sent by Agent Pi

        Returns:
            (dict) results, including rc and account
        '''

        if data["state"] == "in-use":
            search_state = "reserved"
            position = None
        elif data["state"] == "returned":
            search_state = "in-use"
            position = {
                "location": data["location"],
                "latitude": data["latitude"],
                "longitude": data["longitude"]
            }
        else:
            return {"rc": -1}

        # authenticate user account
        if "encodings" in data:
            # by facial recognition
            encodings = [numpy.array(
                x) for x in data["encodings"]] if data["encodings"] is not None else None
            account = self._faceRecogAccount(encodings)
        else:
            # by account/password
            account = self._authAccount(data["username"], data["password"])
        if account is None:
            return {"rc": -1}

        # search for the booking that matches the account and the car
        booking = self._searchBooking(account["id"], data["id"], search_state)
        if booking is None:
            return {"rc": -1}

        # update the booking details
        if self._updateBooking(booking["id"], data["state"], position) != 0:
            return {"rc": -1}

        return {
            "rc": 0,
            "account": account
        }

    def _faceRecogAccount(self, encodings):
        '''Authenticate user account by facial recognition

        Args:
            encodings (list) : a list of features of faces

        Returns:
            (dict) account that facial recognition model matches, or None if not found
        '''

        if encodings is None:
            return None

        # make sure only one face appearing on the photo
        if len(encodings) != 1:
            return None

        # load training model
        model_file = os.path.join(
            os.path.dirname(__file__), "encodings.pickle")
        with open(model_file, "rb") as f:
            model = pickle.loads(f.read())

        # perform facial recognition matching
        matches = face_recognition.compare_faces(
            model["encodings"], encodings[0])
        if True not in matches:
            return None

        matchedIdxs = [i for (i, b) in enumerate(matches) if b]
        counts = {}
        for i in matchedIdxs:
            name = model["names"][i]
            counts[name] = counts.get(name, 0) + 1

        # select the user with highest likelihood
        rest_data = {
            "username": max(counts, key=counts.get)
        }
        resp = RestUtils.execRestApi("account", "GET", data=rest_data)
        if resp is None or resp["rc"] != 0 or len(resp["data"]) == 0:
            return None

        return resp["data"][0]

    def _authAccount(self, username, password):
        '''Authenticate user account by username/password

        Args:
            username (str) : login account
            password (str) : login password

        Returns:
            (dict) account that username/password match, or None if not found
        '''

        rest_data = {
            "username": username
        }
        resp = RestUtils.execRestApi("account", "GET", data=rest_data)
        if resp is None or resp["rc"] != 0 or len(resp["data"]) == 0:
            return None

        account = resp["data"][0]
        if not check_password_hash(account["password"], password):
            return None

        return account

    def _searchBooking(self, account_id, car_id, state):
        '''Search for the booking that matches the account and the car

        Args:
            account_id (int) : account id
            car_id     (int) : car id
            state      (str) : order state

        Returns:
            (dict) the booking wanted, or None if not found
        '''

        rest_data = {
            "account_id": account_id,
            "car_id": car_id,
            "state": state
        }
        resp = RestUtils.execRestApi("booking", "GET", data=rest_data)
        if resp is None or resp["rc"] != 0:
            return None

        bookings = resp["data"]
        now = datetime.utcnow()
        for booking in bookings:
            # check if it's the right time to unlock/return the car
            pickup_dt = datetime.strptime(
                booking["pickup_time"], "%a, %d %b %Y %H:%M:%S %Z")
            if now >= pickup_dt and now < pickup_dt + timedelta(hours=booking["hours"]):
                return booking

        return None

    def _updateBooking(self, booking_id, state, position):
        ''' Update the booking details

        Args:
            booking_id (int)  : booking id
            state      (str)  : order state
            position   (dict) : geo location

        Returns:
            (int) return code 0 on success, or non-zero on failure
        '''

        rest_data = {
            "id": booking_id,
            "state": state
        }
        if position is not None:
            rest_data.update(position)
        resp = RestUtils.execRestApi("booking", "PUT", data=rest_data)
        if resp is None:
            return -1

        return resp["rc"]


def main():
    '''Entry point of Master Pi daemon'''

    daemon = Daemon(DAEMON_ADDR)
    daemon.run()


if __name__ == "__main__":
    main()
