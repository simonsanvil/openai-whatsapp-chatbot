from .agent import OpenAIAgent
from pandas import to_datetime, to_timedelta
from ast import literal_eval
import logging
import re

logging.basicConfig()
logger = logging.getLogger("APP")
logger.setLevel(logging.DEBUG)

def process_agent_reply(chat_agent:OpenAIAgent,prompt:str,max_response_length:int=150):
    if to_datetime("now")-to_datetime(chat_agent.conversation_start_time) > to_timedelta(3,'h'):
        logger.debug("Its been a while since your last conversation. Restarting conversation")
        chat_agent.start_conversation()
    if re.match('.*speak with (?P<word_after>\w+).*',prompt.lower()):
        logger.debug("Checking if it is needed to switch engine for prompt: "+prompt)
        word_after = match.group('word_after')
        logger.debug(f"Checking if {word_after} is an available engine")
        if word_after.lower() in chat_agent.available_engines:
            print(chat_agent.available_engines)
            logger.debug(f"{word_after} is an available engine")
            prev_conversation = chat_agent.conversation
            chat_agent.set_gtp3_params(engine=word_after.lower())
            if chat_agent.agent_name.lower() in chat_agent.available_engines:
                chat_agent.agent_name = word_after.upper()
            chat_agent.start_conversation()
            reply = f"You are now speaking with {word_after}\n"
            chat_agent.set_conversation(prev_conversation+chat_agent.make_chat_prompt(prompt)+reply)
            return reply
        else:
            logger.debug(f"'{word_after}' is not an available engine")
    
    params_str = '|'.join(['engine','temperature','top_p','max_tokens','max_length','length'])
    regex = f'.*(set|change) (?P<parameter>{params_str}|parameter (\w+)) (to|as) (?P<value>\w+).*\.'
    change_parameter_match = re.match(regex,prompt.lower())
    if change_parameter_match:
        match = change_parameter_match
        if 'parameter' in match.group(0):
            parameter = match.group(3)
        else:
            parameter = match.group('parameter')        
        
        try:
            value = literal_eval(match.group('value'))
        except ValueError:
            value = match.group('value')
        if 'length' in parameter:
            parameter = "max_tokens"
        chat_agent.set_gtp3_params(**{parameter:value})
        if parameter=='engine':
            if chat_agent.agent_name.lower() in chat_agent.available_engines:
                chat_agent.agent_name = value.upper()
        logger.debug(f"parameter {parameter} with value {value} was set correctly")
        return "Okay. It is set"
        
    if prompt.lower().strip()=="restart conversation":
        chat_agent.start_conversation()
        return '[conversation history wont be considered anymore]'
        
    logger.debug(f'Message Received: "{prompt}"')
    reply = chat_agent.chat(prompt,max_response_length)
    logger.debug(f'Response Obtained: "{reply}"')
    return reply