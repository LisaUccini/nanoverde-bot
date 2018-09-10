#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os
import time
import re
import string
import sys
import datetime
from time import strftime
from slackclient import SlackClient



# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None
info_user_tag = []
events_list = [["domani alle 18 apre il nanoverde", 3, datetime.time(18, 0)], ["apertura", 4, 2]]

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
AWARD_COMMAND = "premio"
PRESENTATION_COMMAND = "ciao sono "
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
TIME_TAG = 1



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
    if command.startswith(AWARD_COMMAND):
        response = verify_award(command, event)
    else:
        if command.startswith(PRESENTATION_COMMAND):
            response = new_user(comando,event)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=event["channel"],
        text=response or default_response
    )

def verify_award(comando, event):
    """
        verify if the user has already collected the award
    """
    response = "Non hai ancora ritirato il premio"
    utente = ricerca_utente(event['channel'])

    if utente != "":
        oggi = datetime.datetime.today()
        stoday = oggi.strftime("%y-%m-%d")
        stoday = "20"+stoday
        f = open("../nanoverde/documento.txt", "r")
        leggi = f.readlines()
        f.close()

        for i, val in enumerate(leggi):
            premio = string.split(val, ";")
            data = premio[1]
            data = string.split(data, "\n")
            data = data[0]
            if data == stoday:
                if utente == premio[0]:
                    response = "Hai già ritirato il premio"

    else:
        response = "Non ti conosco, presentati"

    return response

def new_user(comando, event):
    """
        Executes bot command to presentation new user
    """
    global info_user_tag
    code = event["channel"]
    user = comando[2]
    user = user.encode('utf-8')
    risposta = "Benvenuta, " + comando[2]
    
    #open file containing the information of each user
    #example file -> code tag;name user;code slack
    f = open("../nanoverde/utenti.txt", "r")
    file = f.readlines()
    f.close()
    result = ""
    #verify that the user does not already exist
    for i,var in enumerate(file):
        line = string.split(var,"\n")
        appo = line[0]
        appo = string.split(appo,";")
        if appo[1] == user:
            if len(appo) == 3:
                if appo[2] == code:
                    return "Già ti conosco "+ user
                else:
                    return "Conosco già "+ user+" e non sei te"
            else:
                var = line[0] + ";" + code + "\n"
                f = open("../nanoverde/utenti.txt", "w")
                file.append(result)
                for i , var in enumerate(file):
                    f.write(var)
                f.close()
                return risposta
        else:
            if  len(appo) == 3:
                if appo[2] == code:
                    risposta = "Non sei "+ user +", sei "+ appo[1]
                    return risposta

    #only if the user has not been found
    if info_user_tag == []:
        risposta = user + ", hai "+ str(TIME_TAG) +" minuti per passare 5 volte il tag"
        start = time.time()
        final = start + (60 * TIME_TAG)
        info_user_tag.append(user)
        info_user_tag.append(code)
        info_user_tag.append(start)
        info_user_tag.append(final)
    else:
        risposta = "in questo momento sto aggiungendo un'altro utente, ritenta tra 5 minuti"

    return risposta

def add_user_tag():
    """
        Tag acquisition and new user addition
    """

    global info_user_tag
    print info_user_tag
    f = open("../nanoverde/tagpassed.txt", "r")
    tagf = f.readlines()
    f.close()
    solution = []
    find = True 
    result = "" 

    #research tag in file
    #example file: tag code;time(%H:%M)
    text = "ERRORE: il tag non è stato passato correttamente"
    if tagf != []:
        for i,var in enumerate(tagf):
            if var != "" or var != "\n":
                tag_time = string.split(var, ";")
                time = tag_time[1]
                time = string.split(time, "\n")
                time = time [0]
                if time < str(info_user_tag[3]) and time > str(info_user_tag[2]):
                    solution.append(tag_time[0])

        if len(solution) >= 5:
            result = solution[0]
            for i , var in enumerate(solution):
                if result != var:
                    find=False
                    continue
    else:
        find = False
            
        
    #check if the tag was found
    
    if find:
        text = "Benvenuta " + info_user_tag[0]
        utente = result + ";" + info_user_tag[0] + ";" + info_user_tag[1] + "\n"
        f = open("../nanoverde/utenti.txt", "r")
        file=f.readlines()
        f.close()
        f = open("../nanoverde/utenti.txt", "w")
        file.append(utente)
        for i , var in enumerate(file):
            f.write(var)
        f.close()

    slack_client.api_call(
        "chat.postMessage",
        channel=info_user_tag[1],
        text= text
    )
    info_user_tag = []

def ricerca_utente(code):
    """
        search for user name from the slack code
    """
    f = open("../nanoverde/utenti.txt", "r")
    file_utenti = f.readlines()
    f.close()
    for i,val in enumerate(file_utenti):
        user = string.split( val, ";")
        if len(user)==3:
            slack_utente = user[2]
            slack_utente = string.split( slack_utente , "\n")
            slack_utente = slack_utente[0]
            if slack_utente == code:
                return user[1]
    return ""

def periodic_events():
    """
        generates periodic events
    """

    global events_list
    daynow = datetime.date.today().weekday()
    timenow = datetime.datetime.now()
    hours = timenow.hour
    minutes = timenow.minute
    seconds = timenow.second

    f = open("../nanoverde/utenti.txt", "r")
    file_utenti = f.readlines()
    f.close()
    text = []

    if hours > 9 and hours < 22:

        #research and analysis of events
        for i, val in enumerate(events_list):
            if len(val) == 3:
                if type(val[2]) == int:
                    if hours % val[2] == 0: #and daynow == val[1]:
                        if val[0] == "apertura":
                            text.append("il nanoverde apre tra " + str(18-hours) + "h")
                else:
                    if hours == val[2].hour and minutes == val[2].minute and seconds == val[2].second and daynow == val[1]:
                        text.append(val[0])
                

        #write events to known channels
        for i, val in enumerate(file_utenti):
            val = string.split(val, ";")
            if len(val) == 3:
                for j, var in enumerate(text):
                    print var
                    event_channel = string.split(val[2], "\n")
                    event_channel = event_channel[0]
                    slack_client.api_call(
                        "chat.postMessage",
                        channel = event_channel,
                        text = var
                    )


if __name__ == "__main__":
    # instantiate Slack client
    
    slack_client = SlackClient('xoxb-430388344151-429397040834-7v98qoQ2YdPhnl0tMfOINadl')
    
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            periodic_events()
            if not(info_user_tag == []):
                if time.time() > info_user_tag[3]:
                    add_user_tag()
            command, event = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, event)
            time.sleep(RTM_READ_DELAY)

    else:
        print("Connection failed. Exception traceback printed above.")