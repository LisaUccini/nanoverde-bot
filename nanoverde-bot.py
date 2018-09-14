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
import ConfigParser



# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# constants
INFO_USER_TAG = []
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM



def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
        The command is considered only if the nanoverde is called or if 
        the user has already presented itself
    """
    for event in slack_events:
        print "evento"	    
        if event["type"] == "message" and not "subtype" in event:
            print "mesage"	    
            print event["user"]    
            message = event["text"]	          
            user_id=""	
            slack_user = research_code()  
            print slack_user
            for i in slack_user:   
                print "entrato"   
                if not event["user"] == i:
                    print "no"	            
                    user_id, message = parse_direct_mention(event["text"])	
                if user_id == bot_id or event["user"] == i:	   
                    print "si"
                    print message       
                    return message, event
            user_id, message = parse_direct_mention(event["text"])	
            if user_id == bot_id :	      
                return message, event
    return None, None


def research_code():
    slack_user = []
    f = open(parameters["utenti_path"],"r")
    users = f.readlines()
    f.close()
    su = None
    for i in users:
        users_split = string.split(i, ";")
        if len(users_split) == 3:
            print "okix"
            su = users_split[2]
            su = string.split(su, "\n")
            su = su[0]
            slack_user.append(su)
    return slack_user



def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, event, parameters):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    help_response = "possibili comandi: \nciao sono <nome-utente> - Presentati al bot nanoverde in modo che possa riconoscerti\npremio - per sapere se hai già ritirato il premio\nciao nano - \ncome stai? - \nNatale - quanti giorni mancano a Natale?\napertura - quanto tempo manca all'apertura del nanoverde\nore mancati - quante ore mi mancano per poter prendere il premio"
    default_response = "Scusa, non ho capito o non ti conosco"
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    comando = command.rsplit(" ")
    utente = ricerca_utente(event["user"], parameters)

    if command.startswith(parameters["PRESENTATION_COMMAND"]):
        if len(comando) >= 3:
            response = new_user(comando,event, parameters)

    if command.startswith(parameters["CIAO_COMMAND"]):
        if utente is None:
            response = "ciao,io sono nanoverde-bot. Sono bello, basso, verde e regalo cibo e bevande a chi è stato bravo. Te chi sei? non ti conosco"
        else:
             response = "ciao "+ricerca_utente(event["user"], parameters)+", io sono nanoverde-bot. Sono bello, basso, verde e regalo cibo e bevande a chi è stato bravo."

    if command.startswith(parameters["COMESTAI_COMMAND"]):
        response = "io bene, te?"
                
    if command.startswith(parameters["NATALE_COMMAND"]):
        oggi = datetime.datetime.now()
        natale = datetime.datetime.strptime('12/24/2018', "%m/%d/%Y")
        gg = natale - oggi
        oggi = oggi.strftime("%y/%m/%d")
        response = "Oggi è il "+str(oggi)+", mancano solo "+str(gg.days)+" a Natale!!"

    if command.startswith(parameters["APERTURA_COMMAND"]):
        response = open_nano(parameters)

    if command.startswith(parameters["HELP_COMMAND"]):
        response = help_response

    if utente != None :
        if command.startswith(parameters["AWARD_COMMAND"]):
            response = verify_award(command, event,parameters)

        if command.startswith(parameters["MISSINGH_COMMAND"]):
            response = missing_hours(event,parameters) 
    
    # if parameters["ANSWER_ALWAYS"] == "False" and response == None:
    #     response = default_response

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=event["channel"],
        text=response
    )

def missing_hours(event, parameters):
    """
        Executes bot command to calculate missing hours to collect the prize
    """
    utente = ricerca_utente(event["user"], parameters)
    number_day = datetime.datetime.today().weekday()
    daynow = datetime.datetime.today()
    
    if number_day == int(parameters["OPEN_DAY"]):
        delta_l = datetime.timedelta(days = int(parameters["OPEN_DAY"]))
        v = daynow
        l = v - delta_l
    if number_day < int(parameters["OPEN_DAY"]):
        delta_l = datetime.timedelta(days = (number_day))
        l = daynow - delta_l
        delta_v = datetime.timedelta(days = (int(parameters["OPEN_DAY"]) - number_day))
        v = daynow + delta_v
    if number_day == 0:
        l = daynow
        delta_v = datetime.timedelta(days = (int(parameters["OPEN_DAY"])))
        v = daynow + delta_l
    if number_day > int(parameters["OPEN_DAY"]):
        delta_l = datetime.timedelta(days = number_day)
        delta_v = datetime.timedelta(days = number_day - int(parameters["OPEN_DAY"]))
        v = daynow - delta_v
        l = daynow - delta_l

    v = v.strftime("%Y-%m-%d")
    l = l.strftime("%Y-%m-%d")
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

        missing = 35 - totaleOre

        response = "Ti mancano "+ str(missing) +" ore"
        return response
    response = "Errore nella richiesta al server"  + str(r.status_code)
    return response

def open_nano(parameters):
    """
        Executes bot command to calculate how much is missing at the opening of the nanoverde
    """
    daynow = datetime.date.today().weekday()
    timenow = datetime.datetime.now()
    hours = timenow.hour
    minutes = timenow.minute
    seconds = timenow.second
    hrs = 0
    day = 0
    aperto = False
    if daynow == int(parameters["OPEN_DAY"]):
        if hours < int(parameters["OPEN_HOUR"]):
            hrs = int(parameters["OPEN_HOUR"]) - hours
        else:
            aperto = True
    else:
        if daynow < int(parameters["OPEN_DAY"]):
            day = ((int(parameters["OPEN_DAY"]) + 1) - daynow) -1
            if hours < int(parameters["OPEN_HOUR"]):
                hrs = int(parameters["OPEN_HOUR"]) - hours
            else:
                hrs = (24 - hours) + int(parameters["OPEN_HOUR"])
                day = day - 1
        else:
            day = (int(parameters["OPEN_DAY"])) + (6-daynow)
            if hours < int(parameters["OPEN_HOUR"]):
                hrs = (int(parameters["OPEN_HOUR"]) - hours) -1
            else:
                hrs = (24 - hours) + int(parameters["OPEN_HOUR"])
                day = day + 1
    min = 0
    sec = 0
    min = 60 - minutes
    if seconds > 0 :
        if min > 0:
            min = min -1
        sec = 60 - seconds

    response = "mancano solo "+ str(day)+" giorni, "+ str(hrs) +" ore, "+ str(min) + " minuti, "+ str(sec) +" secondi all'apertura del nanoverde"
    if aperto:
        response = "Il nanoverde è aperto adesso"
    
    return response
                       


def verify_award(comando, event, parameters):
    """
        verify if the user has already collected the award
    """
    USER = 0
    DATA = 1

    response = "Non hai ancora ritirato il premio"
    utente = ricerca_utente(event['user'], parameters)

    if utente != "":
        oggi = datetime.datetime.today()
        stoday = oggi.strftime("%Y-%m-%d")
        f =  open(parameters["doc_path"], "r")
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

def new_user(comando, event, parameters):
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
    continua = True
    
    #open file containing the information of each user
    #example file -> code tag;name user;code slack
    f = open(parameters["utenti_path"], "r")
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
                        continua = False
                        return "Già ti conosco "+ user
                        continue
                    else:
                        continua = False
                        return "Conosco già "+ user+" e non sei te"
                        continue
                else:
                    user_code = line[0] + ";" + code + "\n"
                    f =  open(parameters["utenti_path"], "w")
                    with f:
                        for j,var in enumerate(file):
                            if i == j:
                                var = user_code
                            f.write(var)
                        f.close
                    continua = False
                    return risposta
                    continue
            else:
                if  len(appo) == 3:
                    if appo[SLACK_USER] == code:
                        print "wtf"
                        risposta = "Non sei "+ user +", sei "+ appo[UTENTE]
                        continua = False
                        return risposta
                        continue

    #only if the user has not been found
    print continua
    if INFO_USER_TAG == [] and continua:
        risposta = "passa 3 volte il tag, hai "+ str(parameters["TIME_TAG"]) + "minuti"
        start = time.time()
        final = start + (60 * int(parameters["TIME_TAG"]))
        INFO_USER_TAG.append(user)
        INFO_USER_TAG.append(code)
        INFO_USER_TAG.append(start)
        INFO_USER_TAG.append(final)
        INFO_USER_TAG.append(event["channel"])
    else:
        risposta = "in questo momento sto aggiungendo un'altro utente, ritenta tra 5 minuti"

    return risposta

def add_user_tag(parameters):
    """
        Tag acquisition and new user addition
    """
    START = 2
    FINAL = 3
    USER = 0
    USER_SLACK = 1
    CHANN = 4
    global INFO_USER_TAG

    f =  open(parameters["tag_path"], "r")
    with f:
        tagf = f.readlines()
        f.close

    solution = {}
    find = True 
    result = "" 

    #research tag in file
    #example file: tag code;time(%H:%M)
    if tagf != []:
        for var in tagf:
            tag_time = string.split(var, ";")
            if len(tag_time) == 2:
                time = tag_time[1]
                time = string.split(time, "\n")
                time = time [0]
                if time < str(INFO_USER_TAG[FINAL]) and time > str(INFO_USER_TAG[START]):
                    if tag_time[0] in solution:
                        solution[tag_time[0]] = (solution[tag_time[0]]+1)
                    else:
                        solution[tag_time[0]] = 1
        #da controllare
        maxi = 0
        code_max = 0 
        solution[code_max] = maxi
        for i in solution:
            if solution[i] > maxi:
                maxi = solution[i]
                code_max = i
        
        if solution[code_max] < 3:
            find = False

    else:
        find = False
            
    #check if the tag was found
    
    if find:
        text = "Benvenuta " + INFO_USER_TAG[USER]
        utente = code_max + ";" + INFO_USER_TAG[USER] + ";" + INFO_USER_TAG[USER_SLACK] + "\n"
        f =  open(parameters["utenti_path"], "r")
        with f:
            file=f.readlines()
            f.close
        f = open(parameters["utenti_path"], "w")
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
    solution = {}
    return find

def ricerca_utente(code, parameters):
    """
        search for user name from the slack code
    """
    f = open(parameters["utenti_path"], "r")
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
            if len(val) == parameters["OPEN_DAY"]:
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

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


if __name__ == "__main__":
    conf_path = "/etc/nanoverde.bot.conf"
    Config = ConfigParser.ConfigParser()
    Config.read(conf_path)
    Config.sections()
    parameters = {}
    parameters["utenti_path"] = ConfigSectionMap("path")["utenti_path"]
    parameters["tag_path"] = ConfigSectionMap("path")["tag_path"]
    parameters["doc_path"] = ConfigSectionMap("path")["doc_path"]
    parameters["APERTURA_COMMAND"] = ConfigSectionMap("command")["apertura_command"]
    parameters["AWARD_COMMAND"] = ConfigSectionMap("command")["award_command"]
    parameters["CIAO_COMMAND"] = ConfigSectionMap("command")["ciao_command"]
    parameters["COMESTAI_COMMAND"] = ConfigSectionMap("command")["comestai_command"]
    parameters["PRESENTATION_COMMAND"] = ConfigSectionMap("command")["presentation_command"]
    parameters["NATALE_COMMAND"] = ConfigSectionMap("command")["natale_command"]
    parameters["HELP_COMMAND"] = ConfigSectionMap("command")["help_command"]
    parameters["MISSINGH_COMMAND"] = ConfigSectionMap("command")["missingh_command"]
    parameters["TIME_TAG"] = ConfigSectionMap("parameters")["time_tag"]
    parameters["OPEN_DAY"] = ConfigSectionMap("parameters")["open_day"]
    parameters["OPEN_HOUR"] = ConfigSectionMap("parameters")["open_hour"]
    parameters["ANSWER_ALWAYS"] = ConfigSectionMap("parameters")["answer_always"]
    parameters["TOKEN"] = ConfigSectionMap("parameters")["token"]
    print parameters

    events_list = [["domani alle 18 apre il nanoverde", 3, datetime.time(18, 0), ['DCNCW4E0P']], ["apertura", 4, 3, ['DCNCW4E0P']]]
    
    slack_client = SlackClient(parameters["TOKEN"])
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            periodic_events(events_list)
            if INFO_USER_TAG != []:
                print "tag"
                trovato = add_user_tag()
                if time.time() > INFO_USER_TAG[3]:
                    slack_client.api_call(
                        "chat.postMessage",
                        channel = INFO_USER_TAG[4],
                        text = "Errore, il tag non è stato passato correttamente"
                    )   
                    INFO_USER_TAG = []   
                if trovato:
                    INFO_USER_TAG = []
                    
            command, event = parse_bot_commands(slack_client.rtm_read())
            if command:
                print "arrivato comando"
                handle_command(command, event, parameters)
            time.sleep(RTM_READ_DELAY)

    else:
        print("Connection failed. Exception traceback printed above.")