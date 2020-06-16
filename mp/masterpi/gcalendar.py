from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from datetime import timedelta
from masterpi.restutils import RestUtils


class GCalendar:

    API_SERVICE_NAME = "calendar"
    API_VERSION = "v3"
    CALENDAR_ID = "primary"
    EVENT_VERSION = 0

    @classmethod
    def _getService(cls, credentials):
        cred = Credentials(**credentials)
        service = build(GCalendar.API_SERVICE_NAME,
                        GCalendar.API_VERSION, credentials=cred)

        return service

    @classmethod
    def _genEventId(cls, account_id, booking_id, pickup_dt):
        ts = int(datetime.timestamp(pickup_dt))
        return "css%da%db%dt%d" % (GCalendar.EVENT_VERSION, account_id, booking_id, ts)

    @classmethod
    def addEvent(cls, data):
        service = GCalendar._getService(data["credentials"])
        pickup_dt = datetime.strptime(
            data["booking"]["pickup_time"], "%a, %d %b %Y %H:%M:%S %Z")
        return_dt = pickup_dt + timedelta(hours=data["booking"]["hours"])
        event_id = GCalendar._genEventId(
            data["account"]["id"], data["booking"]["id"], pickup_dt)
        desc = "Account:\n"
        desc += "  %(first_name)s %(last_name)s (%(username)s) / %(email)s\n\n" % (
            data["account"])
        desc += "Car spec:\n"
        desc += "%(make)s | %(body_type)s | %(colour)s | %(seats)d seats | %(location)s | $%(hourly_rate)0.2f/hr\n\n" % (
            data["car"])
        desc += "Booking details:\n"
        desc += "  Pick up at: %s\n" % (RestUtils.utcToLocal(
            pickup_dt).strftime("%a, %d %b %Y %H:%M"),)
        desc += "  Return by: %s (%d hours)\n" % (RestUtils.utcToLocal(
            return_dt).strftime("%a, %d %b %Y %H:%M"), data["booking"]["hours"])
        desc += "  Total amount: $%.2f" % (data["booking"]["amount"])
        body = {
            "id": event_id,
            "summary": "Car Share System - Booking Notification",
            "description": desc,
            "location": data["car"]["location"],
            "start": {
                "dateTime": pickup_dt.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": return_dt.isoformat(),
                "timeZone": "UTC"
            }
        }

        try:
            event = service.events().insert(
                calendarId=GCalendar.CALENDAR_ID, body=body).execute()
        except Exception as e:
            print(e)

    @classmethod
    def delEvent(cls, data):
        service = GCalendar._getService(data["credentials"])
        pickup_dt = datetime.strptime(
            data["booking"]["pickup_time"], "%a, %d %b %Y %H:%M:%S %Z")
        event_id = GCalendar._genEventId(
            data["account"]["id"], data["booking"]["id"], pickup_dt)

        try:
            event = service.events().delete(
                calendarId=GCalendar.CALENDAR_ID, eventId=event_id).execute()
        except Exception as e:
            print(e)
