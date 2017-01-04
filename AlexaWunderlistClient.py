import sys
import os
import json
import time
from datetime import datetime, timedelta
import calendar

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import wunderpy2
from six import print_

### Setup Instructions ###
#
# 1. Create a new Wunderlist developer application. You'll need its client ID,
#    and the access token for it to access your account.
#
# 2. Set your WUNDERLIST_ACCESS_TOKEN environment variable to a Personal Access Token
#    obtained in the Wunderlist Account Settings. Do the same for WUNDERLIST_CLIENT_ID.
#
# 3. Set WUNDERLIST_LIST_ID to the id for your list.
#    Go to https://a.wunderlist.com/api/v1/lists to find the correct id.
#
# 4. Set WUNDERLIST_USERS for people you want to assign tasks to or add as followers.
#    Go to https://a.wunderlist.com/api/v1/users.
#    Only use first names, and make sure they're unique.
#    The NAMEs need to match the CreateTaskNAME functions in the IntentSchema
#    and Sample Utterances.
#
# 5. Set timezone offset to time difference from GMT. TODO: use pytz to properly
#    handle timezones.

WUNDERLIST_LIST_ID = 123456789123456789

WUNDERLIST_USERS = {
    "Peter":123456789,
    "Charlie":123456789,
    "David":123456789,
    "Elizabeth":123456789,
}

TIMEZONE_OFFSET = -8

def alexa_event_handler(event, *args, **kwargs):
    slots = event["request"]["intent"]["slots"]
    function_name = event["request"]["intent"]["name"]

    # Assignee name is NAME in CreateTaskNAME
    task_assignee_name = function_name.replace("CreateTask", "")

    # Get task name and the target date
    task_title = slots["TaskName"]["value"].capitalize()
    if "value" in slots["TargetDate"]:
        target_date = slots["TargetDate"]["value"]
    else:
        target_date = None

    # Create the task in Wunderlist
    success = create_task(task_assignee_name, task_title, target_date)

    # Determine what Alexa should say back to the user
    # TODO: handle Wunderlist errors
    if success:
        msg = "Added a task for " + task_assignee_name + ". " + task_title + ". "
    else:
        msg = "I'm sorry. There was an error creating the task."

    if target_date:
        msg += "Due date set for " + target_date + "."

    # Constuct response back to Alexa
    response = {
        "version": "1.0",
        "sessionAttributes": {},
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": msg
            },
            "shouldEndSession": True
        }
    }

    return response

def create_task(task_assignee_name, task_title, target_date):
    task_assignee_id = WUNDERLIST_USERS[task_assignee_name]
    task_followers = []
    task_target_date = get_absolute_date(target_date)

    ### You can add special logic to who follows which task
    '''
    if task_assignee_name == "Bob" or task_assignee_name == "Charlie":
        task_followers.append(WUNDERLIST_USERS["David"])
        task_followers.append(WUNDERLIST_USERS["Elizabeth"])

    if task_assignee_name == "Charlie":
        task_followers.append(WUNDERLIST_USERS["Bob"])
    '''

    # Add Task Asignee and AlexaBot as followers
    task_followers.append(task_assignee_id)

    # Debugging: Measure how long the Wunderlist API takes to process
    start_time = time.time()

    api = wunderpy2.WunderApi()
    client = api.get_client(os.environ['WUNDERLIST_ACCESS_TOKEN'], os.environ['WUNDERLIST_CLIENT_ID'])

    result = client.create_task(WUNDERLIST_LIST_ID,
                              task_title,
                              due_date=task_target_date,
                              assignee_id=task_assignee_id)
    client.create_note(result[wunderpy2.Task.ID], "Created by Alexa Bot. Please excuse spelling errors.")
    # Debugging: print task details and API process time
    print_(json.dumps(result, indent=4))
    print("--- Total Wunderlist API Time: %s seconds ---" % (time.time() - start_time))

    #TODO: Handle Errors and return False if there's an error
    return True;

def get_absolute_date(target_date):
    if target_date is None:
        return None
    now = datetime.now()
    date_str = ""

    # Timezone offset TODO: use pytz for proper timezone adjustment
    now = now + timedelta(hours=TIMEZONE_OFFSET)

    # Support utterances in Custom Slot Type TARGET_DATES
    if target_date in ["today", "tonight", "end of day", "end of the day", "the end of the day"]:
        return now.strftime('%Y-%m-%d')
    elif target_date in ["tomorrow", "end of tomorrow", "end of day tomorrow"]:
        new_date = now + timedelta(days=1)
        return new_date.strftime('%Y-%m-%d')
    elif target_date in ["this week", "end of week", "end of the week", "the end of the week", "end of this week"]:
        start = now - timedelta(days=now.weekday())
        new_date = start + timedelta(days=6)
        return new_date.strftime('%Y-%m-%d')
    elif target_date in ["next week", "end of next week", "the end of next week"]:
        start = now - timedelta(days=now.weekday())
        new_date = start + timedelta(days=13)
        return new_date.strftime('%Y-%m-%d')
    elif target_date in ["this month", "end of month", "end of the month", "the end of the month", "end of this month"]:
        date_str = now.strftime('%Y-%m-')
        date_str += str(calendar.monthrange(now.year, now.month)[1])
        return date_str
    elif target_date in ["next month", "end of next month", "the end of next month"]:
        new_date = now + timedelta(days=31)
        date_str = new_date.strftime('%Y-%m-')
        date_str += str(calendar.monthrange(new_date.year, new_date.month)[1])
        return date_str
    else:
        return None


if __name__ == "__main__":
    print("Starting Debug Mode...")
    test_event = {
      "session": {
        "sessionId": "SessionId.XXXXXXX",
        "application": {
          "applicationId": "amzn1.ask.skill.YYYYYYYY"
        },
        "attributes": {},
        "user": {
          "userId": "amzn1.ask.account.ABCDEFGHIJKLMNOP"
        },
        "new": True
      },
      "request": {
        "type": "IntentRequest",
        "requestId": "EdwRequestId.ZZZZZZZZZZZZ",
        "locale": "en-US",
        "timestamp": "2016-12-29T00:28:14Z",
        "intent": {
          "name": "CreateTaskPeter", # Make sure to change this to one of your users
          "slots": {
            "TaskName": {
              "name": "TaskName",
              "value": "Buy some more milk"
            },
            "TargetDate": {
              "name": "TargetDate",
              "value": "tomorrow"
            }
          }
        }
      },
      "version": "1.0"
    }
    print("Running Test Event:")
    print_(json.dumps(test_event))
    print_(json.dumps(alexa_event_handler(test_event, debug_mode=True), indent=4)) #run in debug mode
