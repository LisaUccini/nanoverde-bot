#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os
import time
import re
import string
import sys
import datetime
import requests
from time import strftime
from slackclient import SlackClient



# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# constants
INFO_USER_TAG = []
UTENTI_PATH = "./utenti.txt"
TAG_PATH = "./tagpassed.txt"
DOC_PATH = "./documento.txt"
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
AWARD_COMMAND = "premio"
CIAO_COMMAND ="ciao nano"
COMESTAI_COMMAND = "come stai?"
PRESENTATION_COMMAND = "ciao sono "
APERTURA_COMMAND = "apertura"
NATALE_COMMAND = "Natale"
HELP_COMMAND = "help"
MISSINGH_COMMAND = "ore mancanti"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
TIME_TAG = 1
OPEN_DAY = 4
OPEN_HOUR = 14



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
    global AWARD_COMMAND
    global PRESENTATION_COMMAND
    global CIAO_COMMAND
    global COMESTAI_COMMAND
    global NATALE_COMMAND
    global MISSINGH_COMMAND
    global HELP_COMMAND
    # Default response is help text for the user
    help_response = "possibili comandi: \nciao sono <nome-utente> - Presentati al bot nanoverde in modo che possa riconoscerti\npremio - per sapere se hai già ritirato il premio\nciao nano - \ncome stai? - \nNatale - quanti giorni mancano a Natale?\napertura - quanto tempo manca all'apertura del nanoverde\nore mancati - quante ore mi mancano per poter prendere il premio"
    default_response = "Scusa, non ho capito o non ti conosco"
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    comando = command.rsplit(" ")
    utente = ricerca_utente(event["user"])
    print utente

    if command.startswith(PRESENTATION_COMMAND):
        response = new_user(comando,event)

    if command.startswith(CIAO_COMMAND):
        response = "ciao "+ricerca_utente(event["user"])+", io sono nanoverde-bot. Sono bello, basso, verde e regalo cibo e bevande a chi è stato bravo."
        if utente == "":
            response = response + "Te chi sei? non ti conosco"
    if command.startswith(COMESTAI_COMMAND):
        response = "io bene, te?"
                
    if command.startswith(NATALE_COMMAND):
        oggi = datetime.datetime.now()
        natale = datetime.datetime.strptime('12/24/2018', "%m/%d/%Y")
        gg = natale - oggi
        oggi = oggi.strftime("%y/%m/%d")
        response = "Oggi è il "+str(oggi)+", mancano solo "+str(gg.days)+" a Natale!!"

    if command.startswith(APERTURA_COMMAND):
        response = open_nano()

    if command.startswith(HELP_COMMAND):
        response = help_response
    print utente

    if utente is not None :
        if command.startswith(AWARD_COMMAND):
            response = verify_award(command, event)

        if command.startswith(MISSINGH_COMMAND):
            response = missing_hours(event) 
    
    
        
    print response
    event["channel"]
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=event["channel"],
        text=response or default_response
    )

def missing_hours(event):
    utente = ricerca_utente(event["user"])
    number_day = datetime.datetime.today().weekday()
    daynow = datetime.datetime.today()
    
    if number_day == 4:
        delta_l = datetime.timedelta(days = 4)
        v = daynow
        l = v - delta_l
    if number_day < 4:
        delta_l = datetime.timedelta(days = (number_day))
        l = daynow - delta_l
        delta_v = datetime.timedelta(days = (4 - number_day))
        v = daynow + delta_v
    if number_day == 0:
        l = daynow
        delta_v = datetime.timedelta(days = (4))
        v = daynow + delta_l
    if number_day > 4:
        delta_l = datetime.timedelta(days = number_day)
        delta_v = datetime.timedelta(days = number_day - 4)
        v = daynow - delta_v
        l = daynow - delta_l

    v = v.strftime("%Y-%m-%d")
    l = l.strftime("%Y-%m-%d")
    print l, v
    #dovrei aver sistemato le date ma bo, controllare
    try:
        r = requests.get("https://showtime.develer.com/summary/" +
                         utente+"?from_date="+l+"&to_date="+v)
    except requests.exceptions.ConnectionError:
        print ("Impossibile contattare il server.")
        return False

    if r.status_code == 200:
        a = r.json()
        totaleOre = 0
        for k, o in a.items():
            o = str(o)
            o = o.split('.')
            ore = float(o[1])/60
            totaleOre = totaleOre+ore+float(o[0])

        print totaleOre
        missing = 35 - totaleOre

        response = "Ti mancano "+ str(missing) +" ore"
        return response
    response = "Errore nella richiesta al server"  + str(r.status_code)
    return response

def open_nano():
    daynow = datetime.date.today().weekday()
    timenow = datetime.datetime.now()
    hours = timenow.hour
    minutes = timenow.minute
    seconds = timenow.second
    hrs = 0
    if daynow == 4:
        if hours < OPEN_HOUR:
            hrs = OPEN_HOUR - hours
        else:
            hrs = (24 - hours) + OPEN_HOUR
            day = 6
    else:
        if daynow < OPEN_DAY:
            day = ((OPEN_DAY + 1) - daynow) -1
            if hours < OPEN_HOUR:
                hrs = OPEN_HOUR - hours
            else:
                hrs = (24 - hours) + OPEN_HOUR
                day = day - 1
        else:
            day = (OPEN_DAY) + (6-daynow)
            if hours < OPEN_HOUR:
                hrs = (OPEN_HOUR - hours) -1
            else:
                hrs = (24 - hours) + OPEN_HOUR
                day = day + 1
    min = 0
    sec = 0
    if minutes > 0:
        hrs = hrs - 1
        min = 60 - minutes
    if seconds > 0 :
        if min > 0:
            min = min -1
        sec = 60 - seconds

        
    response = "mancano solo "+ str(day)+" giorni, "+ str(hrs) +" ore, "+ str(min) + " minuti, "+ str(sec) +" secondi all'apertura del nanoverde"
    return response
                       


def verify_award(comando, event):
    """
        verify if the user has already collected the award
    """
    USER = 0
    DATA = 1

    response = "Non hai ancora ritirato il premio"
    utente = ricerca_utente(event['user'])

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
    SLACK_USER =  2
    global INFO_USER_TAG
    code = event["user"]
    user = comando[2]
    user = user.encode('utf-8')
    risposta = "Benvenuta, " + comando[2]
    
    #open file containing the information of each user
    #example file -> code tag;name user;code slack
    f = open(UTENTI_PATH, "r")
    with f:
        file = f.readlines()
        f.close

    #verify that the user does not already exist
    for i,var in enumerate(file):
        line = string.split(var,"\n")
        appo = line[0]
        appo = string.split(appo,";")
        if len(appo) >= 2:
            if appo[UTENTE] == user:
                if len(appo) == 3:
                    if appo[SLACK_USER] == code:
                        return "Già ti conosco "+ user
                    else:
                        return "Conosco già "+ user+" e non sei te"
                else:
                    user_code = line[0] + ";" + code + "\n"
                    f =  open(UTENTI_PATH, "w")
                    with f:
                        for j,var in enumerate(file):
                            if i == j:
                                var = user_code
                            f.write(var)
                        f.close
                    return risposta
            else:
                if  len(appo) == 3:
                    if appo[SLACK_USER] == code:
                        risposta = "Non sei "+ user +", sei "+ appo[UTENTE]
                        return risposta

    #only if the user has not been found
    if INFO_USER_TAG == []:
        out_file = open("tagpassed.txt","w")
        out_file.write("")
        out_file.close()
        risposta = "passa 3 volte il tag, hai "+ str(TIME_TAG) + "minuti"
        start = time.time()
        final = start + (60 * TIME_TAG)
        INFO_USER_TAG.append(user)
        INFO_USER_TAG.append(code)
        INFO_USER_TAG.append(start)
        INFO_USER_TAG.append(final)
        INFO_USER_TAG.append(event["channel"])
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
    USER_SLACK = 1
    CHANN = 4
    global INFO_USER_TAG

    f =  open(TAG_PATH, "r")
    with f:
        tagf = f.readlines()
        f.close

    solution = []
    find = True 
    result = "" 
    print tagf

    #research tag in file
    #example file: tag code;time(%H:%M)
    text = "ERRORE: il tag non è stato passato correttamente"
    if tagf != []:
        for var in tagf:
            tag_time = string.split(var, ";")
            if len(tag_time) == 2:
                time = tag_time[1]
                time = string.split(time, "\n")
                time = time [0]
                if time < str(INFO_USER_TAG[FINAL]) and time > str(INFO_USER_TAG[START]):
                    solution.append(tag_time[0])
        print solution
        if len(solution) >= 3:
            result = solution[0]
            for var in solution:
                if result != var:
                    find=False
                    continue
        else:
            find = False
    else:
        find = False
            
    print find
    #check if the tag was found
    
    if find:
        text = "Benvenuta " + INFO_USER_TAG[USER]
        utente = result + ";" + INFO_USER_TAG[USER] + ";" + INFO_USER_TAG[USER_SLACK] + "\n"
        f =  open(UTENTI_PATH, "r")
        with f:
            file=f.readlines()
            f.close
        f = open(UTENTI_PATH, "w")
        with f:
            file.append(utente)
            f.close
            for var in file:
                f.write(var)

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
                print user[1]
                return user[1]
    return None

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
                    if hours % val[TIME] == 0 and minutes == 0 and seconds == 0 and daynow == val[DAY]:
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
    events_list = [["domani alle 18 apre il nanoverde", 3, datetime.time(18, 0), ['DCNCW4E0P']], ["apertura", 4, 3, ['DCNCW4E0P']]]
    
    slack_client = SlackClient('xoxb-430388344151-429397040834-YwTVHBsQjuvouwg1CjqaPPqs')
    
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