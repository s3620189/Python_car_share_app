from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash
from masterpi import mysql


bp = Blueprint("api", __name__)


def authorisedRequest():
    '''Check if the request issued from an authoised address

    Returns:
        (bool)
    '''

    if current_app.config["ENV"] == "development":
        # no restriction for developmenet environment
        return True
    elif request.remote_addr == "127.0.0.1":
        # allow request only from localhost
        return True

    return False


def createResponse(rc, msg=None, data=None):
    '''Create a unified structure of response data

    Returns:
        (str) JSONified dict structure with rc, msg and data
    '''

    return jsonify({"rc": rc, "msg": msg, "data": data})



@bp.route("/account", methods=["GET", "POST"])
def apiAccount():
    '''RESTful API for account operations

    GET query string:
        id       (int) : account id
        username (str) : login account

    POST data:
        username   (str) : login account
        password   (str) : login password
        first_name (str) : first name
        last_name  (str) : last name
        email      (str) : email address
    '''

    if not authorisedRequest():
        abort(401, "401 Unauthorized")
    
    
    if request.method == "GET":
        sqlstmt = "SELECT * FROM Account"
        values = {}
        where = []
        if "id" in request.args:
            try:
                values["id"] = int(request.args["id"])
                where.append("id = %(id)s")
            except (TypeError, ValueError):
                pass
        if "username" in request.args:
            values["username"] = request.args["username"]
            where.append("username = %(username)s")
        if len(where) > 0:
            sqlstmt += " WHERE " + " AND ".join(where)
    elif request.method == "POST":
        sqlstmt = "INSERT INTO Account (username, password, first_name, last_name, email)"
        values = {
            "username": request.form["username"] if "username" in request.form else None,
            "password": generate_password_hash(request.form["password"]) if "password" in request.form else None,
            "first_name": request.form["first_name"] if "first_name" in request.form else None,
            "last_name": request.form["last_name"] if "last_name" in request.form else None,
            "email": request.form["email"] if "email" in request.form else None
        }
        sqlstmt += " VALUES (%(username)s, %(password)s, %(first_name)s, %(last_name)s, %(email)s)"
        sqlstmt2 = "SELECT LAST_INSERT_ID() AS account_id"
    else:
        print("Debug: method not supported")
        abort(400, "400 Bad Request")

    try:
        db = mysql.get_db()
        cursor = db.cursor()

        if request.method == "POST":
            if cursor.execute(sqlstmt, values) == 1:
                cursor.execute(sqlstmt2)
                response = createResponse(
                    0, msg="account successfully created", data=cursor.fetchone())
                db.commit()
            else:
                response = createResponse(1, msg="failed to create account")
        else:  # GET should never fail
            cursor.execute(sqlstmt, values)
            response = createResponse(
                0, data=cursor.fetchall())  # always a list

        cursor.close()
    except Exception as e:
        print("Debug: %s" % (e,))
        abort(400, "400 Bad Request")

    return response


@bp.route("/car", methods=["GET"])
def apiCar():
    '''RESTful API for car operations

    GET query string:
        id              (int)   : car id
        make            (str)   : brand
        body_type       (str)   : body type
        colour          (str)   : colour
        seats           (int)   : number of seats
        location        (str)   : up-to-date location
        hourly_rate_min (float) : mininum hourly rate for search
        hourly_rate_max (float) : maximum hourly rate for search
        available       (bool)  : is the car available
    '''

    if not authorisedRequest():
        abort(401, "401 Unauthorized")

    if request.method == "GET":
        sqlstmt = "SELECT * FROM Car"
        values = {}
        where = []
        if "id" in request.args:
            try:
                values["id"] = int(request.args["id"])
                where.append("id = %(id)s")
            except (TypeError, ValueError):
                pass
        if "make" in request.args:
            # wildcard search
            values["make"] = "%" + request.args["make"] + "%"
            where.append("make LIKE %(make)s")
        if "body_type" in request.args:
            # wildcard search
            values["body_type"] = "%" + request.args["body_type"] + "%"
            where.append("body_type LIKE %(body_type)s")
        if "colour" in request.args:
            # wildcard search
            values["colour"] = "%" + request.args["colour"] + "%"
            where.append("colour LIKE %(colour)s")
        if "seats" in request.args:
            try:
                values["seats"] = int(request.args["seats"])
                where.append("seats = %(seats)s")
            except (TypeError, ValueError):
                pass
        if "location" in request.args:
            # wildcard search
            values["location"] = "%" + request.args["location"] + "%"
            where.append("location LIKE %(location)s")
        if "hourly_rate_min" in request.args:
            try:
                values["hourly_rate_min"] = float(
                    request.args["hourly_rate_min"])
                where.append("hourly_rate >= %(hourly_rate_min)s")
            except (TypeError, ValueError):
                pass
        if "hourly_rate_max" in request.args:
            try:
                values["hourly_rate_max"] = float(
                    request.args["hourly_rate_max"])
                where.append("hourly_rate <= %(hourly_rate_max)s")
            except (TypeError, ValueError):
                pass
        if "available" in request.args:
            values["available"] = (request.args["available"] == "True")
            where.append("available = %(available)s")
        if len(where) > 0:
            sqlstmt += " WHERE " + " AND ".join(where)
    else:
        print("Debug: method not supported")
        abort(400, "400 Bad Request")

    try:
        cursor = mysql.get_db().cursor()

        cursor.execute(sqlstmt, values)
        response = createResponse(0, data=cursor.fetchall())  # always a list

        cursor.close()
    except Exception as e:
        print("Debug: %s" % (e,))
        abort(400, "400 Bad Request")

    return response


@bp.route("/booking", methods=["GET", "POST", "PUT"])
def apiBooking():
    '''RESTful API for booking operations

    GET query string:
        id         (int) : booking id
        account_id (int) : account id
        car_id     (int) : car id
        state      (str) : order state

    POST data:
        account_id  (int) : account id
        car_id      (int) : car id
        pickup_time (str) : pickup time in %Y-%m-%d %H:%M format
        hours       (int) : hours reserved

    PUT data:
        id        (str)   : booking id
        state     (str)   : order state
        location  (str)   : up-to-date location
        latitude  (float) : geo latitude
        longitude (float) : geo longitude
    '''

    if not authorisedRequest():
        abort(401, "401 Unauthorized")

    
    if request.method == "GET":
        sqlstmt = "SELECT * FROM Booking"
        values = {}
        where = []
        if "id" in request.args:
            try:
                values["id"] = int(request.args["id"])
                where.append("id = %(id)s")
            except (TypeError, ValueError):
                pass
        if "account_id" in request.args:
            try:
                values["account_id"] = int(request.args["account_id"])
                where.append("account_id = %(account_id)s")
            except (TypeError, ValueError):
                pass
        if "car_id" in request.args:
            try:
                values["car_id"] = int(request.args["car_id"])
                where.append("car_id = %(car_id)s")
            except (TypeError, ValueError):
                pass
        if "state" in request.args:
            values["state"] = request.args["state"]
            where.append("state = %(state)s")
        if len(where) > 0:
            sqlstmt += " WHERE " + " AND ".join(where)
    elif request.method == "POST":
        values = {}
        if "account_id" in request.form:
            try:
                values["account_id"] = int(request.form["account_id"])
            except (TypeError, ValueError):
                pass
        if "car_id" in request.form:
            try:
                values["car_id"] = int(request.form["car_id"])
            except (TypeError, ValueError):
                pass
        if "pickup_time" in request.form:
            values["pickup_time"] = request.form["pickup_time"]
        if "hours" in request.form:
            try:
                values["hours"] = int(request.form["hours"])
            except (TypeError, ValueError):
                pass
        sqlstmt = "UPDATE Car SET available = FALSE WHERE id = %(car_id)s AND available = TRUE"
        sqlstmt2 = "INSERT INTO Booking (account_id, car_id, pickup_time, hours, amount)"
        sqlstmt2 += " SELECT Account.id, Car.id, %(pickup_time)s, %(hours)s, Car.hourly_rate * %(hours)s"
        sqlstmt2 += " FROM Account, Car WHERE Account.id = %(account_id)s AND Car.id = %(car_id)s"
        sqlstmt3 = "SELECT LAST_INSERT_ID() AS booking_id"
    elif request.method == "PUT":
        values = {}
        if "id" in request.form:
            try:
                values["id"] = int(request.form["id"])
            except (TypeError, ValueError):
                pass
        if "state" in request.form:
            values["state"] = request.form["state"]
            values["available"] = True if values["state"] in [
                "returned", "canceled"] else False
        if "location" in request.form:
            values["location"] = request.form["location"]
        if "latitude" in request.form:
            try:
                values["latitude"] = float(request.form["latitude"])
            except (TypeError, ValueError):
                pass
        if "longitude" in request.form:
            try:
                values["longitude"] = float(request.form["longitude"])
            except (TypeError, ValueError):
                pass
        sqlstmt = "UPDATE Car, Booking SET Car.available = %(available)s, Booking.state = %(state)s"
        if "location" in values and "latitude" in values and "longitude" in values:
            sqlstmt += ", Car.location = %(location)s, Car.latitude = %(latitude)s, Car.longitude = %(longitude)s"
        sqlstmt += " WHERE Car.id = Booking.car_id AND Booking.id = %(id)s"
    else:
        print("Debug: method not supported")
        abort(400, "400 Bad Request")

    try:
        db = mysql.get_db()
        cursor = db.cursor()

        if request.method == "POST":
            if cursor.execute(sqlstmt, values) == 1 and cursor.execute(sqlstmt2, values) == 1:
                cursor.execute(sqlstmt3)
                response = createResponse(
                    0, msg="booking successfully created", data=cursor.fetchone())
                db.commit()
            else:
                response = createResponse(1, msg="failed to create booking")
        elif request.method == "PUT":
            if cursor.execute(sqlstmt, values) in [1, 2]:
                response = createResponse(0, msg="booking successfully updated", data={
                                          "booking_id": values["id"]})
                db.commit()
            else:
                response = createResponse(1, msg="failed to update booking")
        else:  # GET should never fail
            cursor.execute(sqlstmt, values)
            response = createResponse(
                0, data=cursor.fetchall())  # always a list

        cursor.close()
    except Exception as e:
        print("Debug: %s" % (e,))
        abort(400, "400 Bad Request")

    return response
