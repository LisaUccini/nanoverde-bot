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

# constants
INFO_USER_TAG = []
UTENTI_PATH = "../nanoverde/utenti.txt"
TAG_PATH = "../nanoverde/tagpassed.txt"
DOC_PATH = "../nanoverde/documento.txt"
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
    default_response = "possibili comandi: \nciao sono <nome-utente> - Presentati al bot nanoverde in modo che possa riconoscerti\npremio - per sapere se hai già ritirato il premio "

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
    USER = 0
    DATA = 1

    response = "Non hai ancora ritirato il premio"
    utente = ricerca_utente(event['channel'])

    if utente != "":
        oggi = datetime.datetime.today()
        stoday = oggi.strftime("%Y-%m-%d")
        f =  open(DOC_PATH, "r")
        with f:
            leggi = f.readlines()
            f.close

        for val in leggi:
            premio = string.split(val, ";")
            data = premio[1]
            data = string.split(premio[DATA], "\n")
            data = data[0]
            if data == stoday and utente == premio[USER]:
                    response = "Hai già ritirato il premio"

    else:
        response = "Non ti conosco, presentati"

    return response

def new_user(comando, event):
    """
        Executes bot command to presentation new user
    """
    UTENTE = 1
    CHANN = 2
    global INFO_USER_TAG
    code = event["channel"]
    user = comando[2]
    user = user.encode('utf-8')
    risposta = "Benvenuta, " + comando[2]
    
    #open file containing the information of each user
    #example file -> code tag;name user;code slack
    f = open(UTENTI_PATH, "r")
    with f:
        file = f.readlines()
        f.close

    result = ""
    #verify that the user does not already exist
    for var in file:
        line = string.split(var,"\n")
        appo = line[0]
        appo = string.split(appo,";")
        if appo[UTENTE] == user:
            if len(appo) == 3:
                if appo[CHANN] == code:
                    return "Già ti conosco "+ user
                else:
                    return "Conosco già "+ user+" e non sei te"
            else:
                var = line[0] + ";" + code + "\n"
                f =  open(UTENTI_PATH, "w")
                with f:
                    file.append(result)
                    f.close
                    for var in file:
                        f.write(var)
                return risposta
        else:
            if  len(appo) == 3:
                if appo[CHANN] == code:
                    risposta = "Non sei "+ user +", sei "+ appo[UTENTE]
                    return risposta

    #only if the user has not been found
    if INFO_USER_TAG == []:
        risposta = user + ", hai "+ str(TIME_TAG) +" minuti per passare 5 volte il tag"
        start = time.time()
        final = start + (60 * TIME_TAG)
        INFO_USER_TAG.append(user)
        INFO_USER_TAG.append(code)
        INFO_USER_TAG.append(start)
        INFO_USER_TAG.append(final)
    else:
        risposta = "in questo momento sto aggiungendo un'altro utente, ritenta tra 5 minuti"

    return risposta

def add_user_tag():
    """
        Tag acquisition and new user addition
    """
    START = 2
    FINAL = 3
    USER = 0
    CHANN = 1
    global INFO_USER_TAG

    f =  open(TAG_PATH, "r")
    with f:
        tagf = f.readlines()
        f.close

    solution = []
    find = True 
    result = "" 

    #research tag in file
    #example file: tag code;time(%H:%M)
    text = "ERRORE: il tag non è stato passato correttamente"
    if tagf != []:
        for var in tagf:
            if var != "" or var != "\n":
                tag_time = string.split(var, ";")
                time = tag_time[1]
                time = string.split(time, "\n")
                time = time [0]
                if time < str(INFO_USER_TAG[FINAL]) and time > str(INFO_USER_TAG[START]):
                    solution.append(tag_time[0])

        if len(solution) >= 5:
            result = solution[0]
            for var in solution:
                if result != var:
                    find=False
                    continue
    else:
        find = False
            
        
    #check if the tag was found
    
    if find:
        text = "Benvenuta " + INFO_USER_TAG[USER]
        utente = result + ";" + INFO_USER_TAG[USER] + ";" + INFO_USER_TAG[CHANN] + "\n"
        f =  open(UTENTI_PATH, "r")
        with f:
            file=f.readlines()
            f.close
        f = open(UTENTI_PATH, "w")
        with f:
            file.append(utente)
            f.close
            for var in file:
                f.write(file)

    slack_client.api_call(
        "chat.postMessage",
        channel=INFO_USER_TAG[CHANN],
        text= text
    )
    INFO_USER_TAG = []

def ricerca_utente(code):
    """
        search for user name from the slack code
    """
    f = open(UTENTI_PATH, "r")
    with f:
        file_utenti = f.readlines()
        f.close

    for val in file_utenti:
        user = string.split( val, ";")
        if len(user)==3:
            slack_utente = user[2]
            slack_utente = string.split( slack_utente , "\n")
            slack_utente = slack_utente[0]
            if slack_utente == code:
                return user[1]
    return ""

def periodic_events(events_list):
    """
        generates periodic events
    """
    TEXT = 0
    DAY = 1
    TIME = 2
    CHANN = 3    

    daynow = datetime.date.today().weekday()
    timenow = datetime.datetime.now()
    hours = timenow.hour
    minutes = timenow.minute
    seconds = timenow.second

    response = ""

    if hours > 9 and hours < 22:

        #research and analysis of events and write events to channels
        for val in events_list:
            if len(val) == 4:
                if type(val[TIME]) == int:
                    if hours % val[TIME] == 0 and daynow == val[DAY]:
                        if val[TEXT] == "apertura":
                            response = ("il nanoverde apre tra " + str(18-hours) + "h")
                else:
                    if hours == val[TIME].hour and minutes == val[TIME].minute and seconds == val[TIME].second and daynow == val[DAY]:
                        response = val[0]

                for i in val[CHANN]:
                    slack_client.api_call(
                        "chat.postMessage",
                        channel = i,
                        text = response
                    )

if __name__ == "__main__":
    # instantiate Slack client
    
    #["text", number of day(monday = 0...), time or duration, lista con canali di destinazione ]
    events_list = [["domani alle 18 apre il nanoverde", 3, datetime.time(18, 0), ['DCNCW4E0P']], ["apertura", 4, 2, ['DCNCW4E0P']]]
    
    slack_client = SlackClient('xoxb-430388344151-429397040834-XK6mNosxeRMa3JFZklnuteRe')
    
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            periodic_events(events_list)
            if INFO_USER_TAG != []:
                if time.time() > INFO_USER_TAG[3]:
                    add_user_tag()
            command, event = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, event)
            time.sleep(RTM_READ_DELAY)

    else:
        print("Connection failed. Exception traceback printed above.")