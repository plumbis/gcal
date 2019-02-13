from __future__ import print_function
from datetime import datetime
import argparse
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def auth():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        print("Found Local Creds")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)
    
def generate_flight(flight_key, flight_date, auth):
    
    flights = {
        "am_lgb": {
            "summary": "Flight to SJC",
            "loc": "B6 826",
            "depart": datetime.time(6, 45),
            "arrive": datetime.time(8, 6)
        },
        
        "pm_lgb": {
            "summary": "Flight to SJC",
            "loc": "B6 1926",
            "depart": datetime.time(17, 0),
            "arrive": datetime.time(19, 4)
        },

        "am_sjc": {
            "summary": "Flight to LGB",
            "loc": "B6 825",
            "depart": datetime.time(8, 48),
            "arrive": datetime.time(10, 3)
        },
        
        "pm_sjc": {
            "summary": "Flight to LGB",
            "loc": "B6 1925",
            "depart": datetime.time(19, 57),
            "arrive": datetime.time(21, 10)
        }
    }

    if flight_key not in flights:
        print("Incorrect flight key " + flight_key + " exiting")
        exit(1)
    
    flight = flights[flight_key]

    event = {
        "summary": flight["summary"],
        "location": flight["loc"],
        "start": { 
            "dateTime": datetime.datetime.combine(flight_date, flight["depart"]).isoformat(),
            "timeZone": "America/Los_Angeles"
        },
        "end": { 
            "dateTime": datetime.datetime.combine(flight_date, flight["arrive"]).isoformat(),
            "timeZone": "America/Los_Angeles"
        },
        "reminders": { 
            "useDefault": False,
            "overrides": []
        },
        "attendees": [
            {"email": "l.martin.carroll@gmail.com"}
        ]
    }
    print("Starting: " + str(event["start"]))
    print("Ending: " + str(event["end"]))
    print("")
    auth.events().insert(calendarId="primary", body=event).execute()  # pylint: disable=undefined-variable
    
    if flight_key == "pm_sjc":
        # Because SJC traffic is the fucking worst.
        start_time = (datetime.datetime.combine(flight_date, flight["depart"]) - datetime.timedelta(hours=4)).isoformat(),
    else:
        start_time = (datetime.datetime.combine(flight_date, flight["depart"]) - datetime.timedelta(hours=2)).isoformat()

    event = {
        "summary": "Travel",
        "start": { 
            "dateTime": start_time,
            "timeZone": "America/Los_Angeles"
        },
        "end": { 
            "dateTime": (datetime.datetime.combine(flight_date, flight["arrive"]) + datetime.timedelta(hours=2)).isoformat(),
            "timeZone": "America/Los_Angeles"
        },
        "reminders": { 
            "useDefault": False,
            "overrides": []
        }
    }
    print("Starting: " + str(event["start"]))
    print("Ending: " + str(event["end"]))
    print("")
    auth.events().insert(calendarId="primary", body=event).execute()  # pylint: disable=undefined-variable
    
def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    parser = argparse.ArgumentParser(description="Create calendar invites for flights")
    parser.add_argument("-dd", "--departure", help="date of departure", required=True)
    parser.add_argument("-dt", "--dtime", choices=["am", "pm"], help="am or pm departure flight", required=True)
    parser.add_argument("-rd", "--returnd", help="date of return", required=True)
    parser.add_argument("-rt", "--rtime", choices=["am", "pm"], help="am or pm return flight", required=True)

    cli = parser.parse_args()
    cli.verbose = True
    
    if cli.departure:
        try:
            departure_date = datetime.datetime.strptime(cli.departure + "/" + str(datetime.datetime.now().year), "%m/%d/%Y").date()
        except ValueError:
            print("Date format of " + cli.departure + " doesn't match mm/dd")
            exit(1)
    
    if cli.returnd:
        try:
            return_date = datetime.datetime.strptime(cli.returnd + "/" + str(datetime.datetime.now().year), "%m/%d/%Y").date()
        except ValueError:
            print("Date format of " + cli.returnd + " doesn't match mm/dd")
            exit(1)

    auth_token = auth()

    print("Generating departing flight")
    generate_flight(cli.dtime + "_" + "lgb", departure_date, auth_token)

    print("Generating returning flight")
    generate_flight(cli.rtime + "_" + "sjc", return_date, auth_token)
    
    mv_stay_return = (return_date + datetime.timedelta(days=1)).isoformat()
    event = {
        "summary": "Pete in Mountain View",
        "start": {
            "date": departure_date.isoformat()
        },
        "end": {
            "date": mv_stay_return
        },
        "reminders": { 
            "useDefault": False,
            "overrides": []
        },
        "attendees": [
            {"email": "l.martin.carroll@gmail.com"}
        ]
    }
    print("Generating Mountain View Stay")
    print("Starting: " + str(event["start"]))
    print("Ending: " + str(event["end"]))
    auth_token.events().insert(calendarId="cumulusnetworks.com_1sriavgi7o8fdgb6jiheg5ngm0@group.calendar.google.com", body=event).execute()  # pylint: disable=no-member

if __name__ == '__main__':
    main()
