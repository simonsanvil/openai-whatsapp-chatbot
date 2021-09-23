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
from ..openai_agent.agent_utils import process_message_and_get_reply
from ..utils.twilio_utils import send_whatsapp_message

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

import argparse

logging.basicConfig()
logger = logging.getLogger("APP")
logger.setLevel(logging.DEBUG)

load_dotenv(find_dotenv())
account_sid = os.environ.get("TWILLIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILLIO_AUTH_TOKEN") 
allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS",'').split(",")
twilio_client = Client(account_sid, auth_token)

app = Flask(__name__)
chat_agent = OpenAIAgent(
    engine='davinci-codex',
    agent_name=os.environ.get("AGENT_NAME"),
    chatter_name=os.environ.get("CHATTER_NAME","HUMAN")
)

num_minutes_conversation_expires = int(os.environ.get("CONVERSATION_EXPIRES_MINS",60*3))
max_tokens = int(os.environ.get("MAX_TOKENS",150))
timer_expire_seconds = 60*60*num_minutes_conversation_expires
scheduler = BackgroundScheduler()
atexit.register(lambda: scheduler.shutdown())

@app.route("/whatsapp/receive",methods=['POST'])
def whatsapp_reply():
    if not scheduler.state:
        scheduler.add_job(func=conversation_timer_callback, trigger="interval", seconds=timer_expire_seconds,id='conversation_restart')
        logger.warning("Timer Started")
        scheduler.start()
    else:
        scheduler.remove_job('conversation_restart')
        scheduler.add_job(func=conversation_timer_callback, trigger="interval", seconds=timer_expire_seconds,id='conversation_restart')
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
    reply = process_message_and_get_reply(chat_agent,message,max_tokens)
    logger.info(f'Reply: "{reply}"')

    response = MessagingResponse()
    response.message(reply)
    logger.info("Conversation: \n"+chat_agent.conversation)

    return str(response)

@app.route("/whatsapp/status",methods=['POST'])
def process_status():
    reqvals = request.values
    logger.info(reqvals)
    return jsonify(reqvals)

def conversation_timer_callback():
    '''
    Restarts conversation due to timer
    '''
    logging.info('Restarting conversation due to timer')
    chat_agent.start_conversation()
    send_whatsapp_message(twilio_client,"It's been a while since our last conversation. I've forgotten all about it already")
    scheduler.pause()

if __name__ == '__main__':
    load_dotenv(find_dotenv())
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--to_phone', help="Phone number to send whatsapp message to")
    parser.add_argument('-m', '--msg', help="Whatsapp message to send to phone number")
    args = parser.parse_args()
    account_sid = os.environ.get("TWILLIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILLIO_AUTH_TOKEN") 
    allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS",'').split(",")
    twilio_client = Client(account_sid, auth_token)
    send_whatsapp_message(twilio_client,args['m'],args['p'])
    
