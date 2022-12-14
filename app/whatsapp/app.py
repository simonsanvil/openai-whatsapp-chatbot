import os, logging
import atexit

from functools import partial
import re
from apscheduler.schedulers.background import BackgroundScheduler

from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client 

from openai_agent import OpenAIAgent

import app.whatsapp.utils as wp_utils
from app.processing import process_reply, process_media
from app.whatsapp.chat import Sender, ChatManager

# Load environment variables and configurations for the app
load_dotenv(find_dotenv())
logging.basicConfig()
logger = logging.getLogger('WP-APP')
logger.setLevel(logging.DEBUG)
twilio_client = Client(
    os.environ.get("TWILLIO_ACCOUNT_SID"), 
    os.environ.get("TWILLIO_AUTH_TOKEN"))
start_template = os.environ.get("START_TEMPLATE")
if os.path.exists(start_template):
    # start_template is a file path
    with open(start_template,'r') as f:
        start_template = f.read()
agent_kwargs = dict(
    engine=os.environ.get("GTP_ENGINE","davinci-codex"),
    agent_name=os.environ.get("AGENT_NAME"),
    start_template=start_template)
chat_managers = {} # to store chat managers for each phone number
# instance the app
app = Flask(__name__)

@app.route("/whatsapp/receive",methods=['POST'])
def whatsapp_reply():
    """
    This function receives the request whatsapp message from Twilio, generates a response with the agent,
    and sends it back to Twilio to be sent to the user.
    """
    num_minutes_conversation_expires = int(os.environ.get("CONVERSATION_EXPIRES_MINS",60*3))
    timer_expire_secs = 60*num_minutes_conversation_expires # after n seconds from the last message, the conversation will be restarted
    # get the request values
    reqvals = dict(request.values)
    logger.info(f"Obtained request: {reqvals}")
    # Verify that the request has the correct format and is allowed
    if 'Body' not in reqvals or 'From' not in reqvals:
        logger.error("No body or phone number given")
        return "Bad Request",400
    # check if the phone number is allowed
    contact = wp_utils.verify_phone_number(reqvals.get('From'))
    if not contact:
        logger.error(f"Phone number not allowed: {reqvals.get('From')}")
        return "Receiver not allowed", 403
    # Save to contact book if required
    if os.environ.get('SAVE_TO_CONTACTBOOK','False').lower() == 'true':
        wp_utils.save_to_contactbook(reqvals)
    # get the sender number and message
    sender = Sender(
        reqvals.get('From'),
        reqvals.get('ProfileName',os.environ.get("CHATTER_NAME","HUMAN")), 
        max_image_generations=contact.get('max_image_generations',10), 
        max_messages=float(contact.get('max_messages',"inf")))
    # Get the chat manager for the sender
    if sender.phone_number not in chat_managers:
        # create a new chat manager for the sender
        logger.info(f"Creating new chat for {sender.name} ({sender.phone_number})")
        chat_agent = OpenAIAgent(**agent_kwargs)
        chat_managers[sender.phone_number] = ChatManager(
            chat_agent,
            BackgroundScheduler(),
            timer_expire_secs,
        )
        chat = chat_managers[sender.phone_number]
    else:
        # retrieve the chat manager for the sender
        chat = chat_managers[sender.phone_number]
        logger.info(f"Using existing chat for {sender.name} ({sender.phone_number}) with {len(chat)} chats")
    if 'image_captioning' in contact:
        chat.image_captioning = bool(contact.get('image_captioning'))
    # start a new conversation if the previous one has expired
    if not chat.agent.is_conversation_active:
        # start a new conversation
        chat.agent.start_conversation(sender.name)
    # get and process the message
    message = reqvals.get('Body').strip()
    logger.info(f"Processing incoming message: '{message}' from {sender.name} ({sender.phone_number})")
    # Check if the message contains media and process it accordingly
    if (num_media:=reqvals.get('NumMedia')):
        num_media = int(num_media)
        if num_media > 0:
            # for i in range(num_media): #TODO
            logger.info("message contains media")
            media_url = reqvals.get(f'MediaUrl0')
            media_type = reqvals.get(f'MediaContentType0')
            logger.info(f"Media : {media_url} ({media_type})")
            message = process_media(media_url,media_type)
    # Create a response model that will send the reply back to Twilio
    response = MessagingResponse()
    if not message:
        # if the message is empty, send a default message
        response.message("Sorry, I didn't understand that.")
        return str(response)
    # verify that the sender has not reached the maximum number of messages
    if len(chat) > sender.max_messages:
        response.message("Sorry, you have reached your maximum number of messages. Try again later.")
        logger.warning(f"User {sender.name} ({sender.phone_number}) has reached their maximum number of messages")
        return str(response)
    # start the timer if it is not running - when the timer expires, the conversation will be restarted
    if not chat.scheduler.running:
        chat.scheduler.add_job(func=partial(conversation_timer_callback, chat=chat) , trigger="interval", seconds=timer_expire_secs,id='conversation_restart')
        logger.warning("Timer Started")
        chat.scheduler.start()
        atexit.register(lambda: chat.scheduler.shutdown())
    else:
        # restart the timer in the scheduler when a new message is received
        chat.scheduler.resume()
        chat.scheduler.reschedule_job('conversation_restart', trigger="interval", seconds=timer_expire_secs)
    # if the message contains a captioning request, set the captioning mode
    if (captioning := wp_utils.ensure_captioning(message, chat)):
        response.message(captioning)
        return str(response)
    # process the message and get the reply
    max_tokens = int(os.environ.get("MAX_TOKENS",150))
    reply = process_reply(message,chat.agent,max_response_length=max_tokens)
    # check if the reply contains an image generation prompt and generate the image if so
    reply = wp_utils.ensure_image_generation(reply,chat,sender, twilio_client=twilio_client)
    # send the reply to the user
    logger.info(f'Reply: "{reply}"')
    msg = response.message(reply)
    logger.info("Conversation: \n"+chat.agent.conversation)
    logger.info(response)

    return str(response)

def conversation_timer_callback(chat:ChatManager):
    '''Restarts conversation when the timer expires'''
    logging.info('Restarting conversation due to timer')
    chat.agent.start_conversation()
    send_whatsapp_message(twilio_client,"It's been a while since our last conversation. I've forgotten all about it already")
    chat.scheduler.pause()

def send_whatsapp_message(twilio_client:Client,msg:str,to_phone:str=None,**kwargs):
    '''Sends a one-way whatsapp message via Twillio to the given phone number'''
    if 'allowed_phone_numbers' in kwargs:
        allowed_phone_numbers = kwargs.get('allowed_phone_numbers').split(",")
    else:
        allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS", "").split(",")
    if 'from_phone' in kwargs:
        from_phone = kwargs.get('from_phone')
    else:
        from_phone = os.environ.get('FROM_WHATSAPP_NUMBER')
    if to_phone is None:
        to_phone = os.environ.get('TO_WHATSAPP_NUMBER')
    if allowed_phone_numbers:
        if os.path.exists(allowed_phone_numbers[0]):
            allowed_phone_numbers = open(allowed_phone_numbers[0],'r').read().splitlines()
        if to_phone not in allowed_phone_numbers:
            raise AttributeError("Sending messages to this phone number is not allowed")
        
    if from_phone is None or to_phone is None:
        raise AttributeError('Valid sender and receiver phone numbers must be given')

    message = twilio_client.messages.create( 
        from_=f'whatsapp:{from_phone}',
        body=msg,      
        to=f'whatsapp:{to_phone}' 
    )

    return message

@app.route("/whatsapp/status",methods=['POST'])
def process_status():
    reqvals = request.values
    logger.info(reqvals)
    return jsonify(reqvals)

if __name__ == '__main__':
    import argparse
    from dotenv import load_dotenv, find_dotenv
    
    load_dotenv(find_dotenv())
    parser = argparse.ArgumentParser(description="Send a whatsapp message via Twillio")
    parser.add_argument('-p', '--to_phone', help="Phone number to send whatsapp message to")
    parser.add_argument('-m', '--msg', help="Whatsapp message to send to phone number")
    args = parser.parse_args()
    account_sid = os.environ.get("TWILLIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILLIO_AUTH_TOKEN") 
    allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS",'').split(",")
    twilio_client = Client(account_sid, auth_token)
    send_whatsapp_message(twilio_client,msg=args.msg,to_phone=args.to_phone)