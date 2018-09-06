#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os
import time
import re
import string
import sys
from slackclient import SlackClient



# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
PRESENTATION_COMMAND = "ciao sono "
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            message = event["text"]
            user_id=""
            if not event["channel"] == "DCNCW4E0P":
                user_id, message = parse_direct_mention(event["text"])
            if user_id == bot_id or event["channel"] == "DCNCW4E0P":
                return message, event
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    print matches
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, event):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Scrivere help"

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    comando = command.rsplit(" ")
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    else:
        if command.startswith(PRESENTATION_COMMAND):
            response = new_user(comando,event)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=event["channel"],
        text=response or default_response
    )

def new_user(comando, event):
    """
        Executes bot command to presentation new user
    """
    code = event["user"]
    user = comando[2]
    user = user.encode('utf-8')
    risposta = "Benvenuta, " + comando[2]
    

    f=open("../nanoverde/utenti.txt", "r")
    file=f.readlines()
    f.close()
    risultato=""
    fine = False

    for i,var in enumerate(file):
        line = file[i].split("\n")
        appo = line[0]
        appo = appo.split(";")
        if appo[1] == user:
            if len(appo) == 3:
                if appo[2] == code:
                    return "Già ti conosco "+ user
                else:
                    return "Conosco già "+ user+" e non sei te"
            else:
                fine = True
                file[i] = line[0] + ";" + code + "\n"
            continue

    if not(fine):
        user = user.split("\n")
        user = user[0]
        slack_client.api_call(
            "chat.postMessage",
            channel=event["channel"],
            text= user + ", passa il tag"
        )

        time.sleep(RTM_READ_DELAY)
        f=open("../nanoverde/tagpassed.txt", "r")
        tagf = f.readlines()
        f.close()

        if len(tagf) == 0:
            return "ERRORE: non hai passato il tag correttamente"

        else:
            fine = True
            tag_code = tagf[len(tagf)-1]
            tag_code = tag_code.split("\n")
            tag_code = tag_code[0]

            out_file = open("../nanoverde/tagpassed.txt","w")
            out_file.write("")
            out_file.close()

            risultato = tag_code + ";" + user + ";" + code + "\n"


    if fine:
        f=open("../nanoverde/utenti.txt", "w")
        file.append(risultato)
        for i , var in enumerate(file):
            f.write(file[i])
        f.close()

    return risposta


if __name__ == "__main__":
    # instantiate Slack client
    #print 
    
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
    
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, event = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, event)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")