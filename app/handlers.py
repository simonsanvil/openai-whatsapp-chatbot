import logging
import re
from app.whatsapp.chat import OpenAIChatManager
from chat.clients import ChatClient
from typing import Tuple

from chat.handlers.assemblyai.audio_transcription import transcribe_audio, supported_language_codes
from chat.handlers.openai.completions import language_detection
from chat.handlers.openai import text_to_image as dalle_text_to_image

def verify_image_generation(msg: str) -> Tuple[str, bool]:
    """
    Checks if the reply contains an image generation prompt. 
    Returns the reply without the image generation prompt if the prompt is valid,
    otherwise returns the reply along with a boolean indicating if the prompt is valid.
    """
    if "[img:" not in msg.lower():
        return msg, False
    # get the prompt and real reply from the message '{reply}[image generation: "{prompt}"]'
    img_generation_prompt = re.search(
        # regex to match [img: "prompt"] with any number of spaces between the colon and the quote
        r"\[img:\s*\"(.*)\"\]", msg, flags=re.IGNORECASE

    )
    if img_generation_prompt is None:
        logging.info(f"No matched image generation prompt found for message: {msg}")
        new_msg = re.sub(r"\[img:\s*\"(.*)\"\]", "", msg, flags=re.IGNORECASE)
        if new_msg:
            return new_msg, False
        return msg, False
    img_generation_prompt = img_generation_prompt.group(1)
    new_msg = re.sub(r"\[img:\s*\"(.*)\"\]", "", msg, flags=re.IGNORECASE)
    logging.info(f"Image generation prompt: '{img_generation_prompt}'")
    return new_msg, img_generation_prompt

def verify_and_process_media(message, chat:OpenAIChatManager, check_language:bool=False) -> str:
    """Processes media messages"""
    if message.media is not None: # if the message contains media
        if message.media.is_audio and chat.voice_transcription:
            # if is audio, transcribe it
            chat.logger.info(f"Message contains audio, attempting to transcribe it with language='{chat.transcription_language}'")
            # msg = whisper_transcription(message.media.url, url=True, language=chat.transcription_language)
            try:
                msg = transcribe_audio(message.media.url, language_code=chat.transcription_language, chat=chat, as_json=True)
                if msg is None:
                    return None
                msg = msg.get("text", None)
            except Exception as e:
                chat.logger.error(f"Audio transcription failed: with url {message.media.url} and language {chat.transcription_language}")
                chat.logger.error(f"Error while transcribing audio: {e}")
                msg = None
        elif message.media.is_image and chat.allow_images:
            #TODO: caption images
            chat.logger.info(f"Message contains an image")
            # img_caption = image_captioning(message.media.url, chat, url=True)
            # msg = f"[image of \"{img_caption}\"]"
            msg = None
        else: # otherwise, send None
            msg = None
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

async def check_and_send_image_generation(prompt: str, chat:OpenAIChatManager, client:ChatClient):
    if chat.num_images_generated > chat.max_image_generations:
        chat.add_message("This user has surpassed their maximum number of images generated. Images will no longer be sent.", role="system")
        client.send_message("[You have reached the maximum number of images that you can generate.]", chat.sender.phone_number)
        return False
    # generate the image and send it to the user
    chat.logger.info(f"Generating image for prompt: {prompt}")
    img_url = await dalle_text_to_image(prompt, as_url=True)
    img_body = prompt if chat.caption_images else None
    await client.send_message_async(img_body, chat.sender.phone_number, media_url=img_url, media_type='image')
    chat.num_images_generated += 1

async def ensure_user_language(chat:OpenAIChatManager, text:str=None):
    """Ensures the user language is set accordingly in the chat based on the user's messages"""
    chat.logger.info(f"Checking user language for chat")
    lang = None
    ld_examples = [('I am a cat', 'english'), ('Ich bin ein Kater', 'german'), ('Soy un gato', 'spanish'), ('', 'english'), ('asiodnajkc', 'english')]
    if text is None:
        for msg in chat.messages:
            if msg['role'].lower() == 'user':
                text = msg['content']
                break
    if text is None:
        return False
    lang = language_detection(text, examples=ld_examples)
    chat.logger.info(f"Detected language: {lang}")
    if lang != chat.language:
        chat.logger.info(f"Changing language from {chat.language} to {lang}")
        chat.add_message(f"The language of the user is {lang}. This should be reflected in the messages of the conversation that the assistant sends", role='system')
        # # change all the system or assistant messages to the new language
        # for msg in chat.messages:
        #     if msg['role'].lower() in ['assistant','system']:
        #         msg['content'] = await atext_translation(msg['content'], to=lang, from_=chat.language)
        # chat.end_conversation_phrases = [await atext_translation(phrase, to=lang, from_=chat.language) for phrase in chat.end_conversation_phrases]
        chat.language = lang
    if lang in supported_language_codes:
        chat.transcription_language = lang
    chat.save()
    return True