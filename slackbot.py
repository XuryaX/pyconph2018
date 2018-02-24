import os
import time
import re
from slackclient import SlackClient
from xoxzo.cloudpy import XoxzoClient
import json


# instantiate Slack client
slack_client = SlackClient('TOKEN')
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "call"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

X4_SID = "<X4 SID>"
X4_TOKEN = "<X4 TOKEN>"

xc = XoxzoClient(sid=X4_SID, auth_token=X4_TOKEN)


def x4_call(caller, recipient, message):
    result = xc.call_tts_playback(
       caller=caller,
       recipient=recipient,
       tts_message=message,
       tts_lang="en")

    if result.errors != None:
       # some error happened
        return json.dumps(result.message, indent=4)
    else:
        callid = result.messages[0]['callid']
        result = xc.get_simple_playback_status(callid)
        return json.dumps(result.message, indent=4)

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    #Naive way -> call +919804310469 from +919903198910 message How do you do
    if command.startswith(EXAMPLE_COMMAND):
        commands = command.split(' ')
        recipient = commands[1]
        caller = commands[3]
        message = commands[5]


        response = x4_call(caller, recipient, message)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            print(command, channel)
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
