import os
from flask import Blueprint, g, jsonify
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask import current_app
from werkzeug.security import check_password_hash
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from masterpi.restutils import RestUtils
from masterpi.gcalendar import GCalendar
from .decorator import parse_json, isAdmin, isManager
from .status_code import StatusCode
from contextlib import contextmanager
from masterpi import mysql
from werkzeug.security import generate_password_hash

bp = Blueprint("web", __name__)


@bp.before_app_request
def handle_result():
    # Every request is instantiated globally
    g.sc = StatusCode()
    g.account = activeAccount()


@contextmanager
def db_exec():
    db = mysql.get_db()
    cursor = db.cursor()
    yield cursor
    db.commit()


def activeAccount():
    '''Obtain currently active account from session

    Returns:
        (dict) account or None on failure
    '''

    if "id" in session:
        resp = RestUtils.execRestApi(
            "account", "GET", data={"id": session["id"]})

        if resp is not None and resp["rc"] == 0 and len(resp["data"]) > 0:
            return resp["data"][0]

    return None


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    '''Index (login) page

    GET query string:
        (None)

    POST data:
        un (str) : login account
        pw (str) : login password
    '''

    account = g.account
    if account is not None:
        return redirect(url_for("web.bookings"))

    error = False
    if request.method == "POST":
        rest_data = {
            "username": request.form.get("un"),
        }
        password = request.form.get("pw")
        resp = RestUtils.execRestApi("account", "GET", data=rest_data)

        if resp is not None and resp["rc"] == 0 and len(resp["data"]) > 0:
            account = resp["data"][0]
            if check_password_hash(account["password"], password):
                session.clear()
                session["id"] = account["id"]

                if current_app.testing:
                    out_data = {
                        "type": "success",
                        "msg": "Successfully loged in!",
                        "rdpage": "Booking history",
                        "rdurl": url_for("web.bookings")
                    }

                    return render_template("information.html", data=out_data)
                else:
                    # request OAuth token for Google Calendar
                    return redirect(url_for("web.authorize"))

        error = True

    return render_template("index.html", error=error)


@bp.route("/logout")
def logout():
    '''Logout page

    GET query string:
        (None)
    '''

    session.clear()
    out_data = {
        "type": "success",
        "msg": "Successfully loged out!",
        "rdpage": "Log in",
        "rdurl": url_for("web.index")
    }

    return render_template("information.html", data=out_data)


@bp.route("/enrolment", methods=["GET", "POST"])
def enrolment():
    '''Enrolment page

    GET query string:
        (None)

    POST data:
        un (str) : login account
        pw (str) : login password
        fn (str) : first name
        ln (str) : last name
        em (str) : email address
    '''

    account = g.account
    if account is not None:
        return redirect(url_for("web.bookings"))

    error = False
    if request.method == "POST":
        rest_data = {
            "username": request.form.get("un"),
            "password": request.form.get("pw"),
            "first_name": request.form.get("fn"),
            "last_name": request.form.get("ln"),
            "email": request.form.get("em")
        }
        resp = RestUtils.execRestApi("account", "POST", data=rest_data)

        if resp is not None and resp["rc"] == 0:
            session.clear()
            out_data = {
                "type": "success",
                "msg": "Successfully enroled!",
                "rdpage": "Log in",
                "rdurl": url_for("web.index")
            }

            return render_template("information.html", data=out_data)

        error = True

    return render_template("enrolment.html", error=error)


@bp.route("/bookings")
def bookings():
    '''Booking history page

    GET query string:
        (None)
    '''

    account = g.account
    if account is None:
        return redirect(url_for("web.index"))

    if g.account and g.account.get("role") == "manager":
        return redirect('/manager')

    rest_data = {
        "account_id": account["id"]
    }
    resp = RestUtils.execRestApi("booking", "GET", data=rest_data)

    if resp is not None and resp["rc"] == 0:
        bookings = resp["data"]
        # collect car details for each booking
        for booking in bookings:
            # need to convert time string back to datetime object
            pickup_dt = datetime.strptime(
                booking["pickup_time"], "%a, %d %b %Y %H:%M:%S %Z")
            booking["pickup_time"] = RestUtils.utcToLocal(pickup_dt)

            rest_data = {
                "id": booking["car_id"]
            }
            resp = RestUtils.execRestApi("car", "GET", data=rest_data)

            if resp is not None and resp["rc"] == 0 and len(resp["data"]) > 0:
                booking["car"] = resp["data"][0]
            else:
                booking["car"] = None
    else:
        bookings = None

    out_data = {
        "account": account,
        "bookings": bookings
    }

    return render_template("bookings.html", data=out_data)


@bp.route("/cancel")
def cancel():
    '''Cancel booking and redirect back to booking history page

    GET query string:
        id (int) : booking id
    '''

    account = g.account
    if account is None:
        return redirect(url_for("web.index"))

    rest_data = {
        "id": request.args.get("id"),
        "state": "canceled"
    }
    resp = RestUtils.execRestApi("booking", "PUT", data=rest_data)

    if resp is not None and resp["rc"] == 0:
        rest_data = {
            "id": int(resp["data"]["booking_id"])
        }
        resp = RestUtils.execRestApi("booking", "GET", data=rest_data)

        if resp is not None and resp["rc"] == 0 and len(resp["data"]) > 0:
            if not current_app.testing:
                # delete Google Calendar event
                gcal_data = {
                    "credentials": session["credentials"],
                    "account": account,
                    "booking": resp["data"][0]
                }
                GCalendar.delEvent(gcal_data)

    return redirect(url_for("web.bookings"))


@bp.route("/cars", methods=["GET", "POST"])
@bp.route("/maps", methods=["GET", "POST"])
def cars():
    ''' Cars listed in tabular format or on Google Maps

    GET query string:
        (None)

    POST date:
        mk (str)   : brand
        bt (str)   : body type
        cl (str)   : colour
        st (int)   : number of seats
        lc (str)   : up-to-date location
        hm (float) : mininum hourly rate for search
        hx (float) : maximum hourly rate for search
    '''

    account = g.account
    if account is None:
        return redirect(url_for("web.index"))

    if request.method == "POST":
        rest_data = {
            "make": request.form.get("mk"),
            "body_type": request.form.get("bt"),
            "colour": request.form.get("cl"),
            "seats": request.form.get("st"),
            "location": request.form.get("lc"),
            "hourly_rate_min": request.form.get("hm"),
            "hourly_rate_max": request.form.get("hx"),
            "available": True
        }
    else:
        rest_data = {
            "available": True
        }

    resp = RestUtils.execRestApi("car", "GET", data=rest_data)

    if resp is not None and resp["rc"] == 0:
        cars = resp["data"]
    else:
        cars = None

    out_data = {
        "account": account,
        "search": rest_data,
        "cars": cars
    }

    if "maps" in request.url_rule.rule:
        if len(cars) > 0:
            latitude = 0
            longitude = 0
            for car in cars:
                latitude += car["latitude"]
                longitude += car["longitude"]

            out_data["map_centre"] = {
                "latitude": latitude / len(cars),
                "longitude": longitude / len(cars)
            }
        else:
            out_data["map_centre"] = {
                "latitude": -37.8102,
                "longitude": 144.9628
            }
        return render_template("maps.html", data=out_data)
    else:
        return render_template("cars.html", data=out_data)


@bp.route("/reservation", methods=["GET", "POST"])
def reservation():
    ''' Reservation page

    GET query string:
        id (int) : car id

    POST data:
        cid (int) : car id
        pt  (str) : pickup time in %Y-%m-%d %H:%M format
        hr  (int) : hours reserved
    '''

    account = g.account
    if account is None:
        return redirect(url_for("web.index"))

    if request.method == "GET":
        rest_data = {
            "id": request.args.get("id"),
            "available": True}
    else:  # POST
        rest_data = {
            "id": request.form.get("cid"),
            "available": True
        }
    resp = RestUtils.execRestApi("car", "GET", data=rest_data)

    if resp is None or resp["rc"] != 0 or len(resp["data"]) == 0:
        out_data = {
            "type": "failure",
            "msg": "Car unavailable now!",
            "rdpage": "Cars available",
            "rdurl": url_for("web.cars")
        }

        return render_template("information.html", data=out_data)

    car = resp["data"][0]

    error = False
    if request.method == "POST":
        rest_data = {
            "account_id": account["id"],
            "car_id": car["id"],
            "pickup_time": request.form.get("pt"),
            "hours": request.form.get("hr")
        }
        try:
            pickup_dt = datetime.strptime(
                rest_data["pickup_time"], "%Y-%m-%d %H:%M")
            rest_data["pickup_time"] = RestUtils.localToUtc(
                pickup_dt).strftime("%Y-%m-%d %H:%M")
            rest_data["hours"] = int(rest_data["hours"])
        except (TypeError, ValueError):
            rest_data["pickup_time"] = None
            rest_data["hours"] = None

        resp = RestUtils.execRestApi("booking", "POST", data=rest_data)

        if resp is not None and resp["rc"] == 0:
            rest_data = {
                "id": int(resp["data"]["booking_id"])
            }
            resp = RestUtils.execRestApi("booking", "GET", data=rest_data)

            if resp is not None and resp["rc"] == 0 and len(resp["data"]) > 0:
                if not current_app.testing:
                    # Add Google Calendar event
                    gcal_data = {
                        "credentials": session.get("credentials"),
                        "account": account,
                        "car": car,
                        "booking": resp["data"][0]
                    }
                    GCalendar.addEvent(gcal_data)

            out_data = {
                "type": "success",
                "msg": "Successfully reserved a car!",
                "rdpage": "Booking history",
                "rdurl": url_for("web.bookings"),
            }

            return render_template("information.html", data=out_data)

        error = True

    out_data = {
        "account": account,
        "car": car
    }

    return render_template("reservation.html", error=error, data=out_data)


# OAuth2 reference: https://developers.google.com/identity/protocols/oauth2/web-server#example

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def credentials_to_dict(credentials):
    '''Convert OAuth credentials to dict

    Args:
        credentials (Credential): credentials for updating Google Calendar events

    Returns:
        (dict) credentials in the format that can be stored in session
    '''

    cred = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    return cred


@bp.route("/authorize")
def authorize():
    '''OAuth authorisation page'''

    client_secret_file = os.path.join(
        current_app.root_path, CLIENT_SECRETS_FILE)
    flow = Flow.from_client_secrets_file(client_secret_file, scopes=SCOPES)
    flow.redirect_uri = url_for("web.oauth2callback", _external=True)
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true")
    session["state"] = state

    return redirect(authorization_url)


@bp.route("/oauth2callback")
def oauth2callback():
    '''OAuth callback page'''

    state = session["state"]
    client_secret_file = os.path.join(
        current_app.root_path, CLIENT_SECRETS_FILE)
    flow = Flow.from_client_secrets_file(
        client_secret_file, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for("web.oauth2callback", _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)

    out_data = {
        "type": "success",
        "msg": "Successfully loged in!",
        "rdpage": "Booking history",
        "rdurl": url_for("web.bookings")
    }

    return render_template("information.html", data=out_data)


@bp.route("/editCar", methods=["POST"])
@isAdmin
@parse_json
def edit_car(data):
    car_id = data.get("id")
    if not car_id:
        return jsonify(g.sc.args_missing)
    required_fields = ['make', 'body_type', 'colour', 'seats', 'location',
                       'hourly_rate', 'available', 'longitude', 'latitude', 'car_condition']
    form = {key: data.get(key) for key in required_fields if data.get(key)}
    if len(form.keys()) > 1:
        fileds = ','.join([f"{key}=%s" for key,
                           val in form.items() if key != 'id'])

        sql = f"UPDATE Car SET {fileds} WHERE id=%s "
        try:
            with db_exec() as cursor:
                cursor.execute(sql, [*list(form.values()), car_id])
        except Exception as e:
            print(e)
            return jsonify(g.sc.system_inner_error)

    return jsonify(g.sc.success())


@bp.route("/addCar", methods=["POST"])
@isAdmin
@parse_json
def add_car(data):
    required_fields = ['make', 'body_type', 'colour', 'seats', 'location',
                       'hourly_rate', 'available', 'longitude', 'latitude', 'car_condition']
    data['available'] = '1'
    if [key for key in required_fields if not data.get(key)]:
        return jsonify(g.sc.args_missing)

    form = {key: data.get(key) for key in required_fields if data.get(key)}
    keys = ",".join(form.keys())
    values = form.values()
    symbols = ",".join(['%s'] * len(values))
    sql = f"INSERT INTO Car ( {keys} ) VALUES ( {symbols} )"
    try:
        with db_exec() as cursor:
            cursor.execute(sql, list(values))
    except Exception as e:
        print(e)
        return jsonify(g.sc.system_inner_error)

    return jsonify(g.sc.success())


@bp.route("/deleteCar", methods=["POST"])
@isAdmin
@parse_json
def delete_car(data):
    car_id = data.get("id")
    if not car_id:
        return jsonify(g.sc.args_missing)
    sql = "DELETE FROM Car WHERE id=%s"
    try:
        with db_exec() as cursor:
            cursor.execute(sql, car_id)
    except Exception as e:
        print(e)
        return jsonify(g.sc.system_inner_error)

    return jsonify(g.sc.success())


@bp.route("/account", methods=["GET"])
@isAdmin
def account():
    if g.account.get("role") != "admin":
        return redirect(url_for("web.cars"))
    keys = ["id", "username", "first_name", "last_name", "email", "role"]
    args = [f"{key}='{val}'" for key,
            val in request.args.items() if key in keys and val]
    args_str = " AND ".join(args)

    sql = "SELECT id,username,first_name,last_name,email,role FROM Account WHERE id > 0"
    if args:
        sql = f"{sql} AND {args_str}"
        print(sql)
    with db_exec() as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()

    return render_template("account.html", data={"users": data, "account": g.account})


@bp.route("/addUser", methods=["POST"])
@isAdmin
@parse_json
def add_user(data):
    required_fields = ["username", "first_name",
                       "last_name", "email", "role", "password"]
    if [key for key in required_fields if not data.get(key)]:
        return jsonify(g.sc.args_missing)
    data["password"] = generate_password_hash(data.get("password"))
    form = {key: data.get(key) for key in required_fields if data.get(key)}
    username = form.get('username')
    has_user_sql = "SELECT * FROM Account WHERE username=%s LIMIT 1"
    # Check if the user name is registered
    with db_exec() as cursor:
        cursor.execute(has_user_sql, username)
        has_user = cursor.fetchall()
    if has_user and has_user[0].get('id'):
        return jsonify(g.sc.username_already_exists)
    keys = ",".join(form.keys())
    values = form.values()
    symbols = ",".join(['%s'] * len(values))

    sql = f"INSERT INTO Account ( {keys} ) VALUES ( {symbols} )"
    print(sql)
    try:
        with db_exec() as cursor:
            cursor.execute(sql, list(values))
    except Exception as e:
        print(e)
        return jsonify(g.sc.system_inner_error)

    return jsonify(g.sc.success())


@bp.route("/editUser", methods=["POST"])
@isAdmin
@parse_json
def edit_user(data):
    user_id = data.get("id")
    if not user_id:
        return jsonify(g.sc.args_missing)
    required_fields = ["username", "first_name", "last_name", "email", "role"]
    form = {key: data.get(key) for key in required_fields if data.get(key)}
    if len(form.keys()) > 1:
        fileds = ','.join([f"{key}=%s" for key,
                           val in form.items() if key != 'id'])

        sql = f"UPDATE Account SET {fileds} WHERE id=%s"
        try:
            with db_exec() as cursor:
                cursor.execute(sql, [*list(form.values()), user_id])
        except Exception as e:
            print(e)
            return jsonify(g.sc.system_inner_error)

    return jsonify(g.sc.success())


@bp.route("/deleteUser", methods=["POST"])
@isAdmin
@parse_json
def delete_user(data):
    user_id = data.get("id")
    if not user_id:
        return jsonify(g.sc.args_missing)
    sql = f"DELETE FROM Account WHERE id =%s"
    try:
        with db_exec() as cursor:
            cursor.execute(sql, user_id)
    except Exception as e:
        print(e)
        return jsonify(g.sc.system_inner_error)

    return jsonify(g.sc.success())


@bp.route("/manager", methods=["GET"])
@isManager
def manager():

    return render_template("manager.html", data={"account": g.account})
