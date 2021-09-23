from twilio.rest import Client 
from dotenv import load_dotenv, find_dotenv
import os

def send_whatsapp_message(twilio_client:Client,msg:str,to_phone:str=None,**kwargs):
    '''
    Sends a one-way whatsapp message via Twillio to the given phone number
    '''
    if 'allowed_phone_numbers' in kwargs:
        allowed_phone_numbers = kwargs.get('allowed_phone_numbers')
    else:
        allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS")
    if 'from_phone' in kwargs:
        from_phone = kwags.get('from_phone')
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

    return message.sid