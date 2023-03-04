import os, logging

from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler

from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify

from chat.clients.twilio import TwilioWhatsAppClient, TwilioWhatsAppMessage
from chat.handlers.openai import (
    chat_completion as chatgpt_completion,
    text_to_image as dalle_text_to_image,
    voice_transcription as whisper_transcription,
)
# from chat.handlers.image import image_captioning
from app.handlers import verify_image_generation
from app.whatsapp.chat import Sender, OpenAIChatManager

# Load environment variables and configurations for the app
load_dotenv(find_dotenv())
logging.basicConfig()
logger = logging.getLogger('WP-APP')
logger.setLevel(logging.DEBUG)
# chat agent configuration
system_message_template = os.environ.get("CHATGPT_SYSTEM_MSG")
if os.path.exists(system_message_template):
    with open(system_message_template,'r') as f:
        system_message_template = f.read()
chat_options = dict(
    model=os.environ.get("CHAT_MODEL","gpt-3.5-turbo"),
    agent_name=os.environ.get("AGENT_NAME"),
    system_message=system_message_template,
    goodbye_message="Goodbye! I'll be here if you need me.")
from_number=os.environ.get("TWILLIO_WHATSAPP_NUMBER","+14155238886")
# instance the app
app = Flask(__name__)

@app.route("/whatsapp/reply",methods=['POST'])
async def reply_to_whatsapp_message():
    logger.info(f"Obtained request: {dict(request.values)}")
    # create the chat manager
    sender = Sender(phone_number=request.values.get('From'), name=request.values.get('ProfileName', request.values.get('From')))
    chat = OpenAIChatManager.get_or_create(sender, **chat_options)
    # chat.scheduler.a
    # create the chat client
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    chat_client = TwilioWhatsAppClient(
        account_sid, 
        auth_token, 
        from_number=from_number,
        allow_voice_messages=True, 
        allow_images=True, 
        **chat_options)
    chat.system_message = chat_options.get('system_message').format(
        user=sender.name,
        today=datetime.now().strftime('%Y-%m-%d')
    )
    chat.messages[0] = chat.make_message(chat.system_message, role='system')
    # parse and process the message
    new_message = chat_client.parse_request_values(request.values)
    msg = verify_and_process_media(new_message, chat)
    # check if the conversation should end
    if check_conversation_end(msg, chat):
        chat_client.send_message(
            chat.goodbye_message.format(user=sender.name),
            chat.sender.phone_number)
        return jsonify({'status':'ok'})
    if msg is None:
        # if the message is empty, send a default response
        reply = "Sorry, I didn't understand that. Please try again."
        chat_client.send_message(msg, chat.sender.phone_number)
        return jsonify({'status':'ok'})
    # generate the reply
    chat.add_message(msg, role='user')
    reply = chatgpt_completion(chat.messages, model='gpt-3.5-turbo').strip()
    logger.info(f"Generated reply: {reply}")
    # check if the reply is requesting an image generation
    reply, img_prompt = verify_image_generation(reply)
    # send the reply
    chat_client.send_message(reply, chat.sender.phone_number, on_failure="Sorry, I didn't understand that. Please try again.")
    # add the reply to the chat
    chat.add_message(reply, role='assistant')
    # if the reply was requesting an image generation, send the image
    if img_prompt and chat.num_images_generated < chat.max_image_generations:
        #TODO: if the number of images generated surpasses the max, send a system message that alerts this to the assistant
        # generate the image and send it to the user
        logger.info(f"Generating image for prompt: {img_prompt}")
        img_url = dalle_text_to_image(img_prompt, as_url=True)
        img_body = img_prompt if chat.caption_images else None
        await chat_client.send_message_async(img_body, chat.sender.phone_number, media_url=img_url, media_type='image')
        chat.num_images_generated += 1
    # save the chat
    chat.save()
    logger.info(f"--------------\nConversation:\n{chat.get_conversation()}\n----------------")
    return jsonify({'status':'ok'})

@app.route("/whatsapp/status",methods=['POST'])
def process_whatsapp_status():
    logger.info(f"Obtained request: {dict(request.values)}")
    return jsonify({'status':'ok'})

def verify_and_process_media(message, chat:OpenAIChatManager) -> str:
    """Processes media messages"""
    if message.media is not None: # if the message contains media
        if message.media.is_audio and chat.voice_transcription:
            # if is audio, transcribe it
            msg = whisper_transcription(message.media.url, url=True, language=chat.transcription_language)
        # elif message.media.is_image and chat.allow_images:
        #     # if is an image, caption it
        #     img_caption = image_captioning(message.media.url, chat, url=True)
        #     msg = f"[image of \"{img_caption}\"]"
        else: # otherwise, just use the message body
            msg = message.body
    else:
        # otherwise, just use the message body
        msg = message.body
    return msg

def check_conversation_end(message:str, chat:OpenAIChatManager) -> bool:
    """Checks if the conversation should end"""
    if message.lower().strip() in chat.end_conversation_phrases:
        chat.restart_conversation()
        return True
    return False

if __name__ == '__main__':
    import argparse
    from dotenv import load_dotenv, find_dotenv
    from twilio.rest import Client 
    
    load_dotenv(find_dotenv())
    parser = argparse.ArgumentParser(description="Send a whatsapp message via Twillio")
    parser.add_argument('-p', '--to_phone', help="Phone number to send whatsapp message to")
    parser.add_argument('-m', '--msg', help="Whatsapp message to send to phone number")
    args = parser.parse_args()
    account_sid = os.environ.get("TWILLIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILLIO_AUTH_TOKEN") 
    allowed_phone_numbers = os.environ.get("ALLOWED_PHONE_NUMBERS",'').split(",")
    twilio_client = Client(account_sid, auth_token)
    # send_whatsapp_message(twilio_client,msg=args.msg,to_phone=args.to_phone)

    # return reply, 200
    # handler = ReplyHandler()
    # handler.add_step(chat_completion)
    # chat.register_handler(handler)