import requests, os
import json
import logging

from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client 

from dotenv import find_dotenv, load_dotenv
from ast import literal_eval

from flask import Flask, request, render_template, url_for, jsonify
from pandas import to_datetime, to_timedelta

from ...utils.async_timer import Timer
from ..openai_agent.agent import OpenAIAgent
from ..openai_agent.agent_utils import process_agent_reply


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
conversation_timer = None
timer_expire_seconds = 60*60*1

@app.route("/whatsapp/receive",methods=['POST'])
def whatsapp_reply():
    reqvals = request.values
    logger.info(reqvals)  
    if 'From' in reqvals:
        if reqvals['From'] not in [allowed_phone_numbers]+['whatsapp:'+p for p in allowed_phone_numbers]:
            return "Receiver not allowed",400
    else:
        return "Receiver not allowed",400
    
    if 'Body' not in reqvals:
        return "Receiver not allowed",400

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

    if conversation_timer is None:
        conversation_timer = Timer("Conversation Timer",timer_expire_seconds,restart_conversation_async,context=chat_agent, expires=True)
    elif conversation_timer.expired:
        conversation_timer.restart()

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

async def restart_conversation_async(timer_name, agent, timer):
    context['count'] += 1
    logging.info('Restarting conversation due to timer: ' + timer_name + ". Seconds awaited: " + timer.seconds_awaited)

    agent.start_conversation()
    timer.cancel()


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
