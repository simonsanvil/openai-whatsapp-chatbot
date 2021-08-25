import requests, os
import json
import logging

from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client 

from dotenv import find_dotenv, load_dotenv
from ast import literal_eval

from flask import Flask, request, render_template, url_for, jsonify
from pandas import to_datetime, to_timedelta

from ..openai_agent.agent import OpenAIAgent
from ..openai_agent.agent_utils import process_agent_reply

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig()
logger = logging.getLogger("APP")
logger.setLevel(logging.DEBUG)

load_dotenv(find_dotenv())
account_sid = os.environ.get("TWILLIO_ACCOUNT_SID") 
auth_token = os.environ.get("TWILLIO_AUTH_TOKEN") 
allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS",'').split(",")
twillio_client = Client(account_sid, auth_token)

app = Flask(__name__)
chat_agent = OpenAIAgent(
    engine='davinci-codex',
    agent_name=os.environ.get("AGENT_NAME"),
    chatter_name=os.environ.get("CHATTER_NAME","HUMAN")
)

timer_expire_seconds = 60*60*3
scheduler = BackgroundScheduler()
atexit.register(lambda: scheduler.shutdown())

@app.route("/whatsapp/receive",methods=['POST'])
def whatsapp_reply():
    if not scheduler.state:
        scheduler.add_job(func=restart_conversation, trigger="interval", seconds=timer_expire_seconds,id='conversation_restart')
        logger.warning("Timer Started")
        scheduler.start()
    else:
        scheduler.remove_job('conversation_restart')
        scheduler.add_job(func=restart_conversation, trigger="interval", seconds=timer_expire_seconds,id='conversation_restart')
        # scheduler.resume()

    reqvals = request.values
    logger.info(reqvals)  
    if 'From' in reqvals:
        if reqvals['From'] not in [allowed_phone_numbers]+['whatsapp:'+p for p in allowed_phone_numbers]:
            return "Receiver not allowed",400
    else:
        return "Bad Request",400
    
    if 'Body' not in reqvals:
        return "Bad Request",400

    sender_number = reqvals.get('From')
    sender_name = reqvals.get('ProfileName','Human')
    message = reqvals.get('Body')
    chat_agent.set_chatter_name(sender_name)

    logger.info(f"Processing incoming message: {message} from {sender_name} ({sender_number})")
    reply = process_agent_reply(chat_agent,message,120)
    logger.info(f'Reply: "{reply}"')

    response = MessagingResponse()
    response.message(reply)
    logger.info("Conversation: "+chat_agent.conversation)

    return str(response)


@app.route("/whatsapp/status",methods=['POST'])
def process_status():
    reqvals = request.values
    logger.info(reqvals)
    return jsonify(reqvals)


@app.route('/receive', methods=['GET', 'POST'])
def receive_whatsapp_message():
    print("Received message")
    logger.info(request.values)
    body = request.values.get('Body',None)
    print(body)
    response = MessagingResponse()
    if body.lower() == "hey":
        response.message("Hey there, nice to hear from you!")
    else:
        response.message("Hey, I can't hear you!")
    print(str(response))
    return str(response)

def restart_conversation():
    logging.info('Restarting conversation due to timer')
    chat_agent.start_conversation()
    send_whatsapp_message("It's been a while since our last conversation. Let me remind you I dont have a very good memory 😅")
    # scheduler.remove_job('conversation_restart')
    scheduler.pause()


def send_whatsapp_message(msg,to_phone=None):
    '''
    Sends a one-way whatsapp message via Twillio to the given phone number
    '''
    from_phone = os.environ.get('FROM_WHATSAPP_NUMBER')
    if to_phone is None:
        to_phone = os.environ.get('TO_WHATSAPP_NUMBER')

    if from_phone is None or to_phone is None:
        raise Exception('Valid sender and receiver phone numbers must be given')

    message = twillio_client.messages.create( 
        from_=f'whatsapp:{from_phone}',  
        body=msg,      
        to=f'whatsapp:{to_phone}' 
    )

    return message.sid


