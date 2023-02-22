import os, time, re
import logging
from ast import literal_eval

import requests

from openai_agent import OpenAIAgent

logger = logging.getLogger(__name__)

def process_reply(prompt: str, chat_agent: OpenAIAgent, max_response_length: int = 150) -> str:
    """
    Parse the prompt and reply with a message obtained from the chat agent
    """
    prompt = prompt.strip()
    engines = chat_agent.get_available_engines()
    
    # Check if prompting an specific agent
    if re.match("ask (" + "|".join(engines) + ") .+", prompt.lower()):
        agent_to_prompt = prompt.lower().split(" ")[1]
        if agent_to_prompt in engines:
            new_prompt = " ".join(agent_to_prompt.split(" ")[3:]).strip()
            logger.debug(f'Prompting "{agent_to_prompt}" agent')
            return chat_agent.prompt_agent(new_prompt, agent_to_prompt)

    # Check if the message is a request to change the engine
    engine_change = ensure_engine_change(prompt, chat_agent, engines)
    if engine_change:
        reply = f"[you are now speaking with {engine_change}]\n"
        prev_conversation = chat_agent.conversation
        chat_agent.set_conversation(
            prev_conversation + chat_agent.make_chat_prompt(prompt) + reply
        )
        return reply
    
    param_change = ensure_param_change(prompt, chat_agent, available_engines=engines)
    if param_change:
        return "[parameter changed correctly]"

    if prompt.lower().strip() == "restart conversation":
        chat_agent.start_conversation()
        return "[conversation history wont be considered anymore]"
    if prompt.lower().strip() == "bye":
        chat_agent.start_conversation()
        return "Bye! See you later."

    logger.debug(f'Message Received: "{prompt}"')
    reply = chat_agent.get_reply(prompt, max_response_length=max_response_length)
    logger.debug(f'Response Obtained: "{reply}"')

    return reply

def process_media(media_url,media_type):
    if media_type.startswith('image'):
        return f"Image: {media_url}"
    elif media_type.startswith('video'):
        return f"Video: {media_url}"
    elif media_type.startswith('audio'):
        return process_audio(media_url)
    else:
        return f"Media: {media_url}"
    
def process_audio(media_url):
    """Use AssemblyAI to transcribe audio"""
    logger.info(f"Attempting to transcribe audio: {media_url}")
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {
        "authorization": os.environ.get('ASSEMBLYAI_API_KEY'),
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=dict(audio_url=media_url), headers=headers)
    response.raise_for_status()
    transcription_id = response.json()['id']
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"
    response = requests.get(endpoint, headers=headers)
    time_now = time.time()
    while (status := response.json()['status']).lower() != 'completed':
        response = requests.get(endpoint, headers=headers)
        if time.time() - time_now > 30: # 30 second timeout
            logger.error(f"Timeout waiting for transcription: {transcription_id}")
            return None
    transcription = response.json()['text']
    logger.info(f"Transcription data: {response.json()}")
    return transcription

def ensure_engine_change(msg, chat_agent, available_engines):
    """Ensure that the engine is changed in the chat agent if the message contains a change engine command"""
    if (match:=re.match(".*speak with (?P<word_after>[A-Za-z0-9-\-\_]+)", msg.lower())):
        candidate_engine = match.group("word_after")
        if candidate_engine.lower() in available_engines:
            chat_agent.set_agent_params(engine=candidate_engine.lower())
            if chat_agent.name.lower() in available_engines:
                chat_agent.name = candidate_engine.upper()
            chat_agent.start_conversation()
            return candidate_engine
    return False

def ensure_param_change(msg, chat_agent, available_engines):
    """Ensure that the engine is changed in the chat agent if the message contains a change engine command"""
    params_str = "|".join(
        ["engine", "temperature", "top_p", "max_tokens", "max_length", "length"]
    )
    regex = f".*(set|change) (?P<parameter>{params_str}|parameter (\w+)) (to|as) (?P<value>\w+).*\."
    change_parameter_match = re.match(regex, msg.lower())
    if change_parameter_match:
        match = change_parameter_match
        if "parameter" in match.group(0):
            parameter = match.group(3)
        else:
            parameter = match.group("parameter")

        try:
            value = literal_eval(match.group("value"))
        except ValueError:
            value = match.group("value")
        if "length" in parameter:
            parameter = "max_tokens"
        chat_agent.set_agent_params(**{parameter: value})
        if parameter == "engine":
            if chat_agent.name.lower() in available_engines:
                chat_agent.name = value.upper()
        logger.debug(f"parameter {parameter} with value {value} was set correctly")
        return True
    return False

