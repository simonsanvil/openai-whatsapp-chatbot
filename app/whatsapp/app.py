import os, logging
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify
from chat.clients.twilio import TwilioWhatsAppClient, TwilioWhatsAppMessage
from chat.handlers.openai import (
    chat_completion as chatgpt_completion,
    # text_completion as chatgpt_completion,
    voice_transcription as whisper_transcription,
)
from app.handlers import (
    check_and_send_image_generation,
    ensure_user_language,
    verify_image_generation,
    verify_and_process_media,
    check_conversation_end,
)
from app.whatsapp.chat import Sender, OpenAIChatManager

# from chat.handlers.image import image_captioning

# Load environment variables and configurations for the app
load_dotenv(find_dotenv())
logging.basicConfig()
logger = logging.getLogger("WP-APP")
logger.setLevel(logging.DEBUG)

# chat agent configuration
start_template = os.environ.get("CHAT_START_TEMPLATE")
if os.path.exists(start_template):
    with open(start_template, "r") as f:
        start_template = f.read()

chat_options = dict(
    model=os.environ.get("CHAT_MODEL", "gpt-3.5-turbo"),
    agent_name=os.environ.get("AGENT_NAME"),
    start_system_message=start_template,
    goodbye_message="Goodbye! I'll be here if you need me.",
    voice_transcription=True,
    allow_images=True,
)
model_options = dict(
    model=os.environ.get("CHAT_MODEL", "gpt-3.5-turbo"),
    max_tokens=int(os.environ.get("MAX_TOKENS", 1000)),
    temperature=os.environ.get("TEMPERATURE", 1.2),
    top_p=int(os.environ.get("TOP_P", 1)),
    frequency_penalty=os.environ.get("FREQUENCY_PENALTY", 0.3),
    presence_penalty=os.environ.get("PRESENCE_PENALTY", 0.1),
    n=1,
)

# create the chat client
chat_client = TwilioWhatsAppClient(
    account_sid=os.environ.get("TWILLIO_ACCOUNT_SID"),
    auth_token=os.environ.get("TWILLIO_AUTH_TOKEN"),
    from_number=os.environ.get("TWILLIO_WHATSAPP_NUMBER", "+14155238886"),
)

# instance the app
app = Flask(__name__)


@app.route("/whatsapp/reply", methods=["POST"])
async def reply_to_whatsapp_message():
    logger.info(f"Obtained request: {dict(request.values)}")
    # create the chat manager
    sender = Sender(
        phone_number=request.values.get("From"),
        name=request.values.get("ProfileName", request.values.get("From")),
    )
    chat = OpenAIChatManager.get_or_create(sender, logger=logger, **chat_options)
    chat.start_system_message = chat_options.get("start_system_message").format(
        user=sender.name, today=datetime.now().strftime("%Y-%m-%d")
    )
    chat.messages[0] = chat.make_message(chat.start_system_message, role="system")
    # parse and process the message
    new_message = chat_client.parse_request_values(request.values)
    msg = verify_and_process_media(new_message, chat)
    # check if the conversation should end
    if message_empty_or_goodbye(msg, chat):
        return jsonify({"status": "ok"})
    # if this is the first message, ensure the language is set
    logger.info("Chat has %d messages", len(chat.messages))
    if len(chat.messages) == 1:
        await ensure_user_language(chat, text=msg)
    # generate the reply
    chat.add_message(msg, role="user")
    reply = chatgpt_completion(chat.messages, **model_options).strip()
    logger.info(f"Generated reply of length {len(reply)}")
    # check if the reply is requesting an image generation
    reply, img_prompt = verify_image_generation(reply)
    # send the reply
    chat_client.send_message(
        reply,
        chat.sender.phone_number,
        on_failure="Sorry, I didn't understand that. Please try again.",
    )
    # add the reply to the chat
    chat.add_message(reply, role="assistant")
    # if the reply was requesting an image generation, send the image
    if img_prompt:
        chat.add_message(f"[img:\"{img_prompt}\"]", role="system")
        await check_and_send_image_generation(img_prompt, chat, client=chat_client)
    # save the chat
    chat.save()
    logger.info(
        f"--------------\nConversation:\n{chat.get_conversation()}\n----------------"
    )
    return jsonify({"status": "ok"})

def message_empty_or_goodbye(msg, chat):
    if check_message_empty(msg, chat):
        reply = "Sorry, I didn't understand that. Please try again."
        chat_client.send_message(reply, chat.sender.phone_number)
        # chat.add_message(reply, role="assistant")
        return True
    if check_conversation_end(msg, chat):
        chat_client.send_message(
            chat.goodbye_message.format(user=chat.sender.name),
            chat.sender.phone_number,
        )
        return True
    return False

def check_message_empty(msg, chat):
    if msg is None or msg.strip() == "":
        # if the message is empty, send a default response
        return True
    return False


@app.route("/whatsapp/status", methods=["POST"])
def process_whatsapp_status():
    logger.info(f"Obtained request: {dict(request.values)}")
    return jsonify({"status": "ok"})
