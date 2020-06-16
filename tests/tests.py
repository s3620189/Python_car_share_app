import os
import sys
import pickle
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath('../mp'))
from masterpi import create_app
from masterpi import api
from daemon import Daemon

sys.path.insert(0, os.path.abspath('../ap'))
from agent import AgentPi
from agent import CONFIG_FILE


class TestAll(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config = {
            "MYSQL_DATABASE_DB": "testdb",
            "SECRET_KEY": "testing",
            "ENV": "development",
            "TESTING": True
        }
        cls.app = create_app(test_config=config)
        cls.ap = AgentPi(CONFIG_FILE)


    @classmethod
    def tearDownClass(cls):
        pass


    def getApiResponseData(self, resp):
        self.assertEqual(resp.status_code, 200)
        content = resp.get_json()
        self.assertEqual(content["rc"], 0)
        return content["data"]
    

    def getwebResponseData(self, resp, status_code=200):
        self.assertEqual(resp.status_code, status_code)
        return resp.data.decode("utf-8")


    def test_01_cli_initdb(self):
        runner = self.app.test_cli_runner()
        resp = runner.invoke(args=["init-db"])
        self.assertTrue("Done." in resp.output)


    def test_02_test_api_account_post(self):
        client = self.app.test_client()

        rest_data = {
            "username": "zhou",
            "password": "1234",
            "first_name": "Xun",
            "last_name": "Zhou",
            "email": "xun.zhou@gmail.com"
        }
        resp = client.post("/api/account", data=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(data["account_id"], 1)


    def test_03_test_api_account_get(self):
        client = self.app.test_client()

        rest_data = {
            "id": 1
        }
        resp = client.get("/api/account", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["username"], "zhou")

        rest_data = {
            "username": "zhou"
        }
        resp = client.get("/api/account", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)


    def test_04_api_car_get(self):
        client = self.app.test_client()

        rest_data = {
            "make": "Holden",
            "body_type": "Sedan",
            "colour": "Grey",
            "seats": 5,
            "location": "Box Hill",
            "hourly_rate_min": 10.00,
            "hourly_rate_max": 11.00,
            "available": True
        }
        resp = client.get("/api/car", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 2)


    def test_05_api_booking_post(self):
        client = self.app.test_client()

        rest_data = {
            "account_id": 1,
            "car_id": 1,
            "pickup_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "hours": 12
        }
        resp = client.post("/api/booking", data=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(data["booking_id"], 1)


    def test_06_api_booking_get(self):
        client = self.app.test_client()

        rest_data = {
            "id": 1
        }
        resp = client.get("/api/booking", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["account_id"], 1)

        rest_data = {
            "account_id": 1,
            "car_id": 1,
            "state": "reserved"
        }
        resp = client.get("/api/booking", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)


    def test_07_api_booking_put(self):
        client = self.app.test_client()

        rest_data = {
            "id": 1,
            "state": "returned",
            "location": "Burwood",
            "latitude": -37.850014,
            "longitude": 145.114129
        }
        resp = client.put("/api/booking", data=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(data["booking_id"], 1)

        rest_data = {
            "id": 1
        }
        resp = client.get("/api/car", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["location"], "Burwood")

        rest_data = {
            "id": 1
        }
        resp = client.get("/api/booking", query_string=rest_data)
        data = self.getApiResponseData(resp)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["state"], "returned")


    def test_08_web_index_get(self):
        client = self.app.test_client()

        resp = client.get("/index")
        data = self.getwebResponseData(resp)
        self.assertTrue("<title>Welcome</title>" in data)


    def test_09_web_index_post(self):
        client = self.app.test_client()

        req_data = {
            "un": "zhou",
            "pw": "1234"
        }
        resp = client.post("/index", data=req_data)
        data = self.getwebResponseData(resp)
        with client.session_transaction() as session:
            self.assertEqual(session["id"], 1)
        self.assertTrue("Successfully loged in!" in data)


    def test_10_web_logout_get(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        resp = client.get("/logout")
        data = self.getwebResponseData(resp)
        with client.session_transaction() as session:
            self.assertTrue("id" not in session)
        self.assertTrue("Successfully loged out!" in data)


    def test_11_web_enrolment_get(self):
        client = self.app.test_client()

        resp = client.get("/enrolment")
        data = self.getwebResponseData(resp)
        self.assertTrue("<title>Enrolment</title>" in data)


    def test_12_web_enrolment_post(self):
        client = self.app.test_client()

        req_data = {
            "un": "bale",
            "pw": "4321",
            "fn": "Christian",
            "ln": "Bale",
            "em": "christian.bale@gmail.com"
        }
        resp = client.post("/enrolment", data=req_data)
        data = self.getwebResponseData(resp)
        self.assertTrue("Successfully enroled!" in data)


    def test_13_web_bookings_get(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        resp = client.get("/bookings")
        data = self.getwebResponseData(resp)
        self.assertTrue("<title>Booking histry</title>" in data)


    def test_14_web_cars_get(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        resp = client.get("/cars")
        data = self.getwebResponseData(resp)
        self.assertTrue("<title>Cars available</title>" in data)


    def test_15_web_maps_post(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        req_data = {
            "mk": "Holden",
            "bt": "Sedan",
            "cl": "Grey",
            "st": 5,
            "lc": "Box Hill",
            "hm": 10.00,
            "hx": 11.00
        }
        resp = client.post("/maps", data=req_data)
        data = self.getwebResponseData(resp)
        self.assertTrue("<title>Cars on Google Maps</title>" in data)


    def test_16_web_reservation_get(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        req_data = {
            "id": 1
        }
        resp = client.get("/reservation", query_string=req_data)
        data = self.getwebResponseData(resp)
        self.assertTrue("<title>Reservation</title>" in data)


    def test_17_web_reservation_post(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        req_data = {
            "cid": 1,
            "pt": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "hr": 12
        }
        resp = client.post("/reservation", data=req_data)
        data = self.getwebResponseData(resp)
        self.assertTrue("Successfully reserved a car!" in data)


    def test_18_web_cancel_get(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["id"] = 1

        req_data = {
            "id": 2
        }
        resp = client.get("/cancel", query_string=req_data)
        data = self.getwebResponseData(resp, status_code=302)
        self.assertTrue('<a href="/bookings">/bookings</a>' in data)


    def test_19_daemon_updateDetails(self):
        client = self.app.test_client()

        rest_data = {
            "account_id": 1,
            "car_id": 1,
            "pickup_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "hours": 12
        }
        resp = client.post("/api/booking", data=rest_data)
        data = self.getApiResponseData(resp)

        req_data = {
            "username": "zhou",
            "password": "1234",
            "state": "in-use",
            "id": 1
        }

        daemon = Daemon()
        with self.app.app_context():
            resp = daemon._updateDetails(req_data)
        self.assertEqual(resp["rc"], 0)
        self.assertEqual(resp["account"]["id"], 1)

        with open("zhou.pickle", "rb") as f:
            encodings = pickle.loads(f.read())
        req_data = {
            "encodings": encodings,
            "state": "returned",
            "id": 1,
            "location": "Blackburn",
            "latitude": -37.821106,
            "longitude": 145.149885
        }
        with self.app.app_context():
            resp = daemon._updateDetails(req_data)
        self.assertEqual(resp["rc"], 0)
        self.assertEqual(resp["account"]["id"], 1)


    def test_20_agent_execute_usernamePassword(self):
        client = self.app.test_client()

        rest_data = {
            "account_id": 1,
            "car_id": 1,
            "pickup_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "hours": 12
        }
        resp = client.post("/api/booking", data=rest_data)
        data = self.getApiResponseData(resp)

        req_data = {
            "username": "zhou",
            "password": "1234",
            "state": "in-use",
            "id": 1
        }
        resp = self.ap._execute(req_data)
        self.assertEqual(resp["rc"], 0)
        self.assertEqual(resp["account"]["id"], 1)


    def test_21_agent_execute_facialRecognition(self):
        req_data = {
            "encodings": [x.tolist() for x in self.ap._extractFaceFeatures("zhou.jpg")],
            "state": "returned",
            "id": 1,
            "location": "Blackburn",
            "latitude": -37.821106,
            "longitude": 145.149885
        }

        resp = self.ap._execute(req_data)
        self.assertEqual(resp["rc"], 0)
        self.assertEqual(resp["account"]["id"], 1)


if __name__ == '__main__':
    unittest.main()
