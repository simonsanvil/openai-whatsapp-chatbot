import os
import logging, copy

import requests
from dotenv import load_dotenv, find_dotenv
import openai

import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Union, List, Any, Dict

logging.basicConfig()


class OpenAIAgent:
    """
    A chatting agent to have a conversation with [OpenAI's](https://beta.openai.com/) GTP models (Codex, Davinci, Ada, ...).

    Parameters:
    -------
    
    chatter_name:str = "Human"
        Name to adress the person at your end of the conversation.

    agent_name:str = None
        Name to adress the agent. Default is the name of the engine (e.g 'davinci','babbage',etc).

    api_key : str = None
        OpenAI's API key. If this attribute is missing then it will read it from an `OPENAI_API_KEY` environmental variable that must be set
        If there's a .env file at the top working directory it will be loaded from here.

    engine:Union['davinci','curie','babbage','ada'] = "davinci"
        GTP Language model engine. "davinci" is the most advanced but also the most expensive (as of summer 2021).

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
    gtp3.set_msg_from("Simon") #name of the human at your end of the conversation
    gtp3.chat("Hi, what's up?")
    print(gtp3.conversation)
    ```

    ```bash
    The following is a conversation with an AI. The AI is helpful, polite, creative, clever, and very friendly. The AI is talking with a person named Simon.

    GTP-3: Hi. My name is GTP-3.
    Simon: Hi, what's up?
    GTP-3: I'm using this conversation to train myself, so thanks for doing this.
    ```
    """

    START_TEMPLATE = (""
#     """
# The following is a conversation with an AI. The AI is helpful, apolitical, clever, and very friendly. 
# Besides chatting with a person, the AI is also capable of generating images. When the person states its desire for the AI to generate an image, 
# the AI will respond with the message "[reply] [image generation: "[prompt]"]" where "[reply]" is a standard reply about the task and "[prompt]" is the prompt/title for the image generation task.
# For example, if the person types "I want to see a picture of a cat", the AI could respond with "Sure, Coming right up! [image generation: "a cat"]". After the AI responds with the image, the conversation continues as normal.
# Another example is if the person types "Can  you show me an image of a dog wearing a hat?", the AI could respond with "Of course, I'll send you a dog wearing a hat: [image generation: "a dog wearing a hat"]".
# One thing to keep in mind is that the images take a few seconds to generate, so the AI will not respond with the image immediately. The AI should not reply as if it has already sent the image.
# The AI's name is {AGENT_NAME} and is talking with {CHATTER}.
#     """.strip()
    )

    # MSG_TEMPLATE = """{chatter_name}:{MSG}\n{AGENT_NAME}:"""
    MSG_TEMPLATE = """{chatter_name}:{MSG}\n{AGENT_NAME}:"""

    def __init__(
        self,
        agent_name: str = None,  # "GTP",
        engine: str = "text-davinci-003",
        start_template: str = None,
        msg_template: str = None,
        api_key: str = None,
        max_response_length: int = 150,
        temperature: float = 0.8,
        top_p: float = 1,
        frequency_penalty: float = 0.3,
        presence_penalty: float = 0.1,
        n_completions_per_prompt: int = 1,
        **extra_params,
    ):
        if api_key is None:
            dotenv_path = find_dotenv()
            load_dotenv(dotenv_path)
            if os.path.isfile(dotenv_path):
                logging.info(".env found and loaded")
            else:
                logging.info(".env not found")

            if "OPENAI_API_KEY" in os.environ:
                api_key = os.environ.get("OPENAI_API_KEY")
                logging.info("OpenAI API key is set in the environmental variables.")
            else:
                logging.warning(
                    "OpenAI API key is not set in the environmental variables."
                )
        elif "OPENAI_API_KEY" not in os.environ:
            os.environ["OPEN_API_KEY"] = api_key

        openai.api_key = api_key
        self.agent_name_ = agent_name if agent_name else engine.upper()
        self.chatter_name = None
        self.START_TEMPLATE = start_template if start_template else self.START_TEMPLATE + "\n"
        self.MSG_TEMPLATE = msg_template if msg_template else self.MSG_TEMPLATE
        if engine not in (available_engines := self.get_available_engines()):
            raise ValueError(f"Engine must be one of {available_engines}")
        self.completion_params = dict(
            engine=engine,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            max_tokens=extra_params.get("max_tokens", max_response_length),
            n=extra_params.get("n", n_completions_per_prompt),
            **extra_params
            # best_of=best_of
        )
        self.__dict__["_conversation__"] = None
        self.__dict__["conversation_start_time"] = datetime.utcnow().isoformat()
        self.__dict__["is_conversation_active"] = False

    @property
    def conversation(self):
        return self._conversation__ or ""

    @property
    def engine(self):
        return self.completion_params["engine"]

    @property
    def agent_name(self):
        return (
            self.agent_name_
            if self.agent_name_ not in self.get_available_engines()
            else self.engine.upper()
        )

    @classmethod
    def get_available_engines(cls):
        """
        Get a list of the engines available to the agent
        """
        if os.environ.get("AVAILABLE_ENGINES"):
            return os.environ.get("AVAILABLE_ENGINES").split(",")
        return cls.get_engines()

    @classmethod
    def get_engines(cls):
        """
        Get a list of the openai api engines
        """
        if not isinstance(cls, OpenAIAgent): # if not instantiated
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        logging.debug("Obtaining list of engines")
        engines_json = openai.Engine.list()
        engines = list(map(lambda x: x["id"], engines_json["data"]))
        return engines

    def __len__(self):
        """Get the number of messages in the conversation"""
        messages = re.findall(rf"{self.chatter_name}:", self.conversation)
        return len(messages)

    def __setattr__(self, name, value):
        if name in [
            "_conversation__",
            "conversation_start_time",
            "is_conversation_active",
        ]:
            raise AttributeError("This attribute is inmutable.")
        self.__dict__[name] = value

    def set_msg_from(self, name):
        """
        Set the name of the user chatting with the agent
        """
        chatter_name = name

    def set_agent_name(self, name):
        """
        Set the name of the agent chatting with the user
        """
        self.agent_name = name

    def set_agent_param(
        self,
        param: str,
        val: Union[float, str],
    ):
        """
        Set parameter `param` of the GTP agent completion to value `val`
        
        For info about the parameters see:
        https://beta.openai.com/docs/api-reference/completions
        """
        self.completion_params[param] = val

    def set_agent_params(self, **params):
        """
        Set the parametets of the GTP agent completions

        For info about the parameters see:
        https://beta.openai.com/docs/api-reference/completions
        """
        for param in params:
            self.completion_params[param] = params[param]

    def with_params(self, **params):
        """
        Returns a new copy of this GTP3Agent object with the given params.
        """
        agent = copy.deepcopy(self)
        agent.set_gtp3_params(**params)
        return agent

    def start_conversation(self, chatter_name: str = None):
        """
        Starts a new conversation history erasing the previous one if there is
        """
        self.__dict__["_conversation__"] = self.START_TEMPLATE.format(
            AGENT_NAME=self.agent_name,
            CHATTER=f"a person named {chatter_name}" if chatter_name else "a human",
        )
        self.__dict__["conversation_start_time"] = datetime.utcnow().isoformat()
        self.__dict__["is_conversation_active"] = True
        self.chatter_name = chatter_name or "HUMAN"

    def set_conversation(self, conversation: str):
        """
        Replaces the previous conversation history with a new conversation history.
        """
        self.__dict__["_conversation__"] = conversation

    def add_to_conversation(self, string):
        """Appends the given string to the conversation history"""
        self.__dict__["_conversation__"] = self.conversation.append(string)

    def make_chat_prompt(self, msg, chatter=None, continue_conversation=True):
        """
        Generate a chat prompt from the message given based on the chat template.
        
        If continue_conversation is True and the conversation history is empty it will inject at the start 
        the starting template, else it will just use the chat message template.
        """
        chatter = chatter or self.chatter_name
        if not self.is_conversation_active or not continue_conversation:
            self.start_conversation()
        prompt = self.MSG_TEMPLATE.format(
            chatter_name=chatter, AGENT_NAME=self.agent_name, MSG=msg.strip()
        )
        return prompt

    def get_completion(self, prompt, stop=None, **kwargs):
        """
        Get openai completion response from a given prompt.

        Params
        -------
        prompt : str
            Text prompt to use for completion.

        max_response_length : int
            Max number of tokens that the text completion will give.

        stop : str|list
            Sequence or list of sequences where the API will stop generating tokens for the response.
        """
        params = self.completion_params.copy()
        params["max_tokens"] = params.get("max_tokens", 150)
        params.update(kwargs)
        completion = openai.Completion.create(prompt=prompt, **params, stop=stop)
        return completion

    def get_single_reply(self, msg, max_response_length=None, chatter_name: str = None):
        """
        Get reply without considering conversation history.

        Params
        -------
        msg : str
            Text message to get a reply to.

        max_response_length : int
            Max number of tokens that a reply will generate.
        """
        chatter_name = chatter_name or self.chatter_name
        new_prompt = self.make_chat_prompt(msg, continue_conversation=False)
        completion = self.get_completion(
            new_prompt,
            max_tokens=max_response_length or self.completion_params.get("max_tokens"),
            stop=[chatter_name + ":", self.agent_name + ":"],
        )
        reply_txt = completion.choices[0].text
        return reply_txt

    def get_reply(self, msg=None, max_response_length=None):
        """
        Get a reply from the chat considering conversation history. 
        If there's no chat history a new one will be made from the template.

        Params
        -------
        msg : str
            Text message to get a reply to and subsequently add to the conversation.
        max_response_length : int
            Max number of tokens that a reply will generate.
        person : str
            Name of the person chatting with the agent. If None the chatter name will be used.
        """
        if msg:
            prompt = self.make_chat_prompt(msg)
        chatter_name = self.chatter_name
        completion = self.get_completion(
            self.conversation + prompt,
            max_tokens=max_response_length or self.completion_params.get("max_tokens"),
            stop=[chatter_name + ":", self.agent_name + ":"],#, "\n"],
        )
        reply_txt = re.sub("(\\n)*$", "", completion.choices[0].text.strip())
        self.update_conversation(msg, reply_txt)
        return reply_txt
    
    def send_message(self, msg):
        """
        Appends a message from the user to the conversation history without getting a reply.

        Params
        -------
        msg : str
            Text message to get a reply to and subsequently add to the conversation.

        Returns
        -------
        None
        """
        self.update_conversation(msg, None)
    
    def update_conversation(self, msg, reply=None):
        """
        Updates the conversation history with a given message and its corresponding reply.
        """
        reply = reply or ""
        self.__dict__["_conversation__"] = (
            self.conversation + self.make_chat_prompt(msg) + reply.strip() + "\n"
        )

    def prompt_agent(
        self, prompt: str, agent: str, max_response_length: int = None, **parameters
    ):
        params = self.completion_params.copy()
        if agent not in self.get_available_engines():
            raise AttributeError(f'"{agent}" is not an available engine.')
        for param in parameters:
            params[param] = parameters[param]
        params["engine"] = agent
        params["max_tokens"] = max_response_length or params.get("max_tokens", 150)
        completion = openai.Completion.create(prompt=prompt.strip(), **params)
        return re.sub("(\\n)*$", "", completion.choices[0].text.strip()).strip()

    def prompt_codex(self, prompt, max_repsonse_length=150, **params):
        return self.prompt_agent(prompt, "davinci-codex", max_repsonse_length, **params)

    def prompt_davinci(self, prompt, max_repsonse_length=150, **params):
        return self.prompt_agent(prompt, "davinci", max_repsonse_length, **params)

    def generate_image(self, prompt: str):
        """
        Generates a new image using the prompt given
        with the image generation API (OpenAI's DALL-E)
        and returns the response.
        """
        # from clients.openai import OpenAIClient

        logging.debug(
            f"Querying OpenAI's Image API 'DALL-E' with prompt '{prompt}'"
        )
        # openai_cl = OpenAIClient()
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        img = response["data"][0]
        img_url = img["url"]
        return img_url

    def copy(self):
        return copy.deepcopy(self)

