import os, logging, json
import atexit
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client 

from gtp_agent import GTPAgent
from gtp_agent.process_msg import process_and_reply

load_dotenv(find_dotenv())

logging.basicConfig()
logger = logging.getLogger("APP")
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
twilio_client = Client(
    os.environ.get("TWILLIO_ACCOUNT_SID"), 
    os.environ.get("TWILLIO_AUTH_TOKEN")
)
chat_agent = GTPAgent(
    engine=os.environ.get("GTP_ENGINE","davinci-codex"),
    agent_name=os.environ.get("AGENT_NAME"),
)
scheduler = BackgroundScheduler()

@app.route("/whatsapp/receive",methods=['POST'])
def whatsapp_reply():
    num_minutes_conversation_expires = int(os.environ.get("CONVERSATION_EXPIRES_MINS",60*3))
    timer_expire_seconds = 60*num_minutes_conversation_expires # 3 hours
    if not scheduler.running:
        scheduler.add_job(func=conversation_timer_callback, trigger="interval", seconds=timer_expire_seconds,id='conversation_restart')
        logger.warning("Timer Started")
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
    else:
        # restart the timer of the scheduler
        scheduler.resume()
        scheduler.reschedule_job('conversation_restart', trigger="interval", seconds=timer_expire_seconds)

    reqvals = request.values
    # reqvals is a CombinedMultiDict, which is a dict-like object that combines multiple dicts
    # We convert it to a regular dict
    reqvals = dict(reqvals)
    logger.info(reqvals)

    allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS",'').split(",")
    if 'From' in reqvals:
        if (phone_number:=reqvals['From']) not in [allowed_phone_numbers]+['whatsapp:'+p for p in allowed_phone_numbers]:
            logger.error(f"Phone number not allowed: {phone_number}")
            return "Receiver not allowed",400
    else:
        logger.error("No phone number given")
        return "Bad Request",400
    
    if 'Body' not in reqvals:
        return "Bad Request",400
    if os.environ.get('SAVE_TO_CONTACTBOOK','False').lower() == 'true':
        save_to_contactbook(reqvals)

    sender_number = reqvals.get('From')
    sender_name = reqvals.get('ProfileName',os.environ.get("CHATTER_NAME","HUMAN"))
    message = reqvals.get('Body')
    logger.info(f"Processing incoming message: {message} from {sender_name} ({sender_number})")    

    if not chat_agent.is_conversation_active:
        chat_agent.start_conversation(sender_name)
        
    max_tokens = int(os.environ.get("MAX_TOKENS",150))
    reply = process_and_reply(message,chat_agent,max_response_length=max_tokens)
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

def send_whatsapp_message(twilio_client:Client,msg:str,to_phone:str=None,**kwargs):
    '''
    Sends a one-way whatsapp message via Twillio to the given phone number
    '''
    if 'allowed_phone_numbers' in kwargs:
        allowed_phone_numbers = kwargs.get('allowed_phone_numbers')
    else:
        allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS")
    if 'from_phone' in kwargs:
        from_phone = kwargs.get('from_phone')
    else:
        from_phone = os.environ.get('FROM_WHATSAPP_NUMBER')
    if to_phone is None:
        to_phone = os.environ.get('TO_WHATSAPP_NUMBER')
    if allowed_phone_numbers:
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

def save_to_contactbook(reqvals):
    '''
    Saves the phone number and name of the sender to the contact book
    '''
    contactbook_path = os.environ.get('CONTACTBOOK_PATH','data/contactbook.json')    
    contactbook = json.load(open(contactbook_path,'r'))
    phone_number = reqvals.get('From')
    name = reqvals.get('ProfileName')
    if phone_number:
        contactbook[phone_number] = {
            "name":name,
            "last_updated":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        json.dump(contactbook,open(contactbook_path,'w'))

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