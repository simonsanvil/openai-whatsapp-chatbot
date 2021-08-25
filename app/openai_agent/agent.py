import os
import logging, copy

import requests
from dotenv import load_dotenv, find_dotenv
import openai

import re
from datetime import datetime
from dataclasses import dataclass
from typing import Union, List

logging.basicConfig()

class OpenAIAgent:
    '''
    A chatting agent to have a conversation with [OpenAI's](https://beta.openai.com/) Codex or GTP models.

    Params
    -------
    
    chatter_name:str = "Human"
        Name to adress the person at your end of the conversation.

    agent_name:str = None
        Name to adress the agent. Default is the name of the engine (e.g 'davinci','babbage',etc).

    api_key : str = None
        OpenAI's API key. If this attribute is missing then it will read it from an `OPENAI_API_KEY` environmental variable that must be set
        If there's a .env file at the top working directory it will be loaded from here.

    engine:Union['davinci','curie','babbage','ada'] = "davinci"
        GTP Language model engine. "davinci" is the most advanced but also the most expensive one.

    temperature : float = 0.9
        Controls randomness: Lowering results in less random completions. As the temperature approaches zero, the model will become deterministic and repetitive.     

    top_p:float = 1
        Controls diversity via nucleus sampling: 0.5 means half of all likelihood-weighted options are considered.

    frequency_penalty:float = 0
        How much to penalize new tokens based on their existing frequency in the text so far. Decreases the model's likelihood to repeat the same line verbatim.

    presence_penalty:float = 0.6
        How much to penalize new tokens based on whether they appear in the text so far. Increases the model's likelihood to talk about new topics.
    
    **params
        Other GTP-3 Parameters. See: https://beta.openai.com/docs/api-reference/parameter-details for a list of all parameters.

    Usage
    ------
    ```python
    gtp3 = GTP3Agent()
    gtp3.set_chatter_name("Simon") #name of the human at your end of the conversation
    gtp3.chat("Hi, what's up?")
    print(gtp3.conversation)
    ```

    ```bash
    The following is a conversation with an AI assistant. The assistant is helpful, polite, creative, clever, and very friendly. The AI is talking with a person named Simon.

    GTP-3: Hi. My name is GTP-3, I'm your AI assistant.
    Simon: Hi, what's up?
    GTP-3: I'm using this conversation to train myself, so thanks for doing this.
    ```
    '''

    START_TEMPLATE = '''
    The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly. The AI is talking with a person named {HUMAN}.
    When the AI doesnt understand a question it replies with "I dont understand".
    {AGENT_NAME}: Hi. My name is {AGENT_NAME}, I'm your AI assistant.
    '''.strip() + '\n'

    MSG_TEMPLATE = '''{HUMAN}: {MSG}\n{AGENT_NAME}: '''

    def  __init__(
            self,
            chatter_name:str="Human",
            agent_name:str=None,#"GTP",
            api_key:str=None,
            engine:Union['davinci','curie','babbage','ada']="davinci",
            temperature:float=0.9,
            top_p:float=1,
            frequency_penalty:float=0,
            presence_penalty:float=0.6,
            **extra_params
        ):
        if api_key is None:
            dotenv_path = find_dotenv()
            load_dotenv(dotenv_path)
            if os.path.isfile(dotenv_path):
                logging.info(".env found and loaded")
            else:
                logging.info('.env not found')
            
            if 'OPENAI_API_KEY' in os.environ:
                api_key = os.environ.get('OPENAI_API_KEY')
                logging.info("OpenAI API key is set in the environmental variables.")
            else:
                logging.warning("OpenAI API key is not set in the environmental variables.")
        elif 'OPENAI_API_KEY' not in os.environ:
            os.environ['OPEN_API_KEY'] = api_key

        #self.api_key = api_key
        openai.api_key = api_key
        self.chatter_name = chatter_name
        self.agent_name_ = agent_name if agent_name else engine.upper()
        self.available_engines = self.get_available_engines()
        self.params = dict(
            engine=engine,
            temperature = temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            **extra_params
            # best_of=best_of
        )
        self.__dict__['_conversation__'] = ""
        self.__dict__['conversation_start_time'] = datetime.utcnow().isoformat()
        self.__dict__['is_conversation_active'] = False
    
    @property
    def conversation(self):
        return self._conversation__
    
    @property
    def engine(self):
        return self.params['engine']
    
    @property
    def agent_name(self):
        return self.agent_name_ if self.agent_name_ not in self.get_available_engines() else self.engine.upper()
    
    def get_available_engines(self):
        if os.environ.get('AVAILABLE_ENGINES') is not None:
            return os.environ.get('AVAILABLE_ENGINES').split(",")
        return self.get_engines()

    def get_engines(self):
        logging.debug("Obtaining list of engines")
        engines_json = openai.Engine.list()
        engines = list(map(lambda x: x['id'],engines_json['data']))
        return engines  
    
    def __setattr__(self, name, value):
        if name in ['_conversation__','conversation_start_time','is_conversation_active']:
            raise AttributeError("This attribute is inmutable.")
        self.__dict__[name] = value
    
    def set_chatter_name(self,name):
        self.chatter_name = name
    
    def set_agent_name(self,name):
        self.agent_name = name
    
    def set_gtp3_param(self,param,val):
        self.params[param]=val

    def set_gtp3_params(self,**params):
        for param in params:
            self.params[param] = params[param]
        
    def with_params(self,**params):
        '''
        Returns a new copy of this GTP3Agent object with the given params.
        '''
        agent = copy.deepcopy(self)
        agent.set_gtp3_params(**params)
        return agent
    
    def start_conversation(self):
        '''
        Starts a new conversation history erasing the previous one if there is
        '''
        self.__dict__['_conversation__'] = self.START_TEMPLATE.format(HUMAN=self.chatter_name,AGENT_NAME=self.agent_name)
        self.__dict__['conversation_start_time'] = datetime.utcnow().isoformat()
        self.__dict__['is_conversation_active'] = True
    
    def set_conversation(self,conversation:str):
        '''
        Replaces the previous conversation history with a new conversation history.
        '''
        self.__dict__['_conversation__'] = conversation
    
    def add_to_conversation(self,string):
        '''Appends the given string to the conversation history'''
        self.__dict__['_conversation__'] = self.conversation.append(string)

    def make_chat_prompt(self,msg,continue_conversation=True):
        '''
        Generate a chat prompt from the message given based on the chat template.
        
        If continue_conversation is True and the conversation history is empty it will inject at the start 
        the starting template, else it will just use the chat message template.
        '''
        prompt = ""
        if not self.is_conversation_active or not continue_conversation:
            self.start_conversation()
            # prompt += self.START_TEMPLATE.format(HUMAN=self.chatter_name,AGENT_NAME=self.agent_name)

        prompt += self.MSG_TEMPLATE.format(HUMAN=self.chatter_name,AGENT_NAME=self.agent_name,MSG=msg)
        return prompt
    
    def get_completion(self,prompt,max_response_length=150,stop=None):
        '''
        Get openai completion response from a given prompt.

        Params
        -------
        prompt : str
            Text prompt to use for completion.

        max_response_length : int
            Max number of tokens that the text completion will give.

        stop : str|list
            Sequence or list of sequences where the API will stop generating tokens for the response.
        '''
        params = self.params.copy()
        params['max_tokens'] = params.get("max_tokens",max_response_length)
        completion = openai.Completion.create(prompt=prompt,**params,stop=stop)
        return completion

    def get_single_reply(self,msg,max_response_length=150):
        '''
        Get reply without considering conversation history.

        Params
        -------
        msg : str
            Text message to get a reply to.

        max_response_length : int
            Max number of tokens that a reply will generate.
        '''
        new_prompt = self.make_chat_prompt(msg,continue_conversation=False)
        completion = self.get_completion(new_prompt,max_response_length,stop=[self.chatter_name+":",self.agent_name+":"])
        reply_txt = completion.choices[0].text
        return reply_txt

    def chat(self,msg,max_response_length=150):
        '''
        Continue chat considering conversation history. If there's no chat history a new one will be made from the template.

        Params
        -------
        msg : str
            Text message to get a reply to and subsequently add to the conversation.

        max_response_length : int
            Max number of tokens that a reply will generate.
        '''
        new_prompt = self.make_chat_prompt(msg)
        completion = self.get_completion(self.conversation+new_prompt,max_response_length,stop=[self.chatter_name+":",self.agent_name+":",'\n'])
        reply_txt = re.sub("(\\n)*$","",completion.choices[0].text.strip())
        self.__dict__['_conversation__'] = self.conversation + new_prompt + reply_txt.strip() + '\n'
        return reply_txt

    

