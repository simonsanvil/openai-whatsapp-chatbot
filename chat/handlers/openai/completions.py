"""
Handlers for OpenAI's Completion and Chat Completion APIs
"""
from typing import List
import openai
import logging
from chat.clients import ChatClient

__all__ = [
    "text_completion",
    "chat_completion",
    "code_generation",
    "whisper_voice_transcription",
    "dalle_text_to_image",
]

def text_completion(
    prompt: str,
    chat: ChatClient = None,
    engine: str = "text-davinci-003",
    **kwargs
):
    """
    Generates text completion using OpenAI's Completion API.

    Parameters
    ----------
    prompt : str
        The prompt to complete.
    chat : ChatClient, optional
        The chat client, by default None
    engine : str, optional
        The engine to use, by default "text-davinci-003"
    **kwargs
        Additional keyword arguments to pass to the Completion API.
        See https://platform.openai.com/docs/api-reference/completions for a list of
        valid parameters.
    """
    logging.info(f"Querying OpenAI's Completion API with prompt '{prompt}'")
    response = openai.Completion.create(
        prompt=prompt,
        engine=engine,
        **kwargs
    )
    return response.get("choices",[{}])[0].get("text")

def chat_completion(
    messages: List[dict],
    chat: ChatClient = None,
    model: str = "gpt-3.5-turbo",
    **kwargs
):
    """
    Generates chat completion using OpenAI's Chat Completion API.

    Parameters
    ----------
    messages : List[dict]
        A list of messages to complete.
    chat : ChatClient, optional
        The chat client, by default None
    model : str, optional
        The model to use, by default "gpt-3.5-turbo"
    **kwargs
        Additional keyword arguments to pass to the Chat Completion API.
        See https://platform.openai.com/docs/api-reference/chat/create for a list of
        valid parameters.
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        **kwargs
    )

    return response.get("choices",[{}])[0].get("message", {}).get("content")

def code_generation(
    prompt: str,
    chat: ChatClient = None,
    engine: str = "davinci-codex",
    **kwargs
):
    """
    Generates code completion using OpenAI's Completion API.
    """
    logging.info(f"Querying OpenAI's Completion API with prompt '{prompt}'")
    response = openai.Completion.create(
        prompt=prompt,
        engine=engine,
        **kwargs
    )
    return response.get("choices",[{}])[0].get("text")