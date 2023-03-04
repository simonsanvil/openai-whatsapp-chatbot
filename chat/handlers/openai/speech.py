import tempfile
from typing import List, Union

import openai
import requests

from chat.clients import ChatClient

def voice_transcription(
    url_or_file: str,
    chat: ChatClient = None,
    *,
    language: str = 'en',
    model: str = 'whisper-1',
    prompt: str = None,
    asynch: bool = False,
    **kwargs
) -> str:
    """
    Transcribes the given audio file or URL using OpenAI's Voice API.
    Returns the transcription as a string.

    Parameters
    ----------
    url_or_file : str
        The URL or path to the audio file to be transcribed.
    chat : ChatClient, optional
        The chat client to use for logging, by default None
    **kwargs
    """
    if url_or_file.startswith("http"):
        response = requests.get(url_or_file)
        response.raise_for_status()
        audio = response.content
        # create the file
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(audio)
        url_or_file = f.name

    params = dict(file=url_or_file,  model=model,  prompt=prompt, language=language, 
                  response_format='json', **kwargs)

    if asynch:
        return openai.Audio.atranscribe(**params)
    
    response = openai.Audio.transcribe(**params)
    return response.get("text")

def voice_translation(
    url_or_file: str,
    chat: ChatClient = None,
    *,
    language: str = 'en',
    model: str = 'whisper-1',
    prompt: str = None,
    **kwargs
) -> str:
    """
    Translates the given audio file or URL using OpenAI's Voice API.
    Returns the translation as a string.

    Parameters
    ----------
    url_or_file : str
        The URL or path to the audio file to be translated.
    chat : ChatClient, optional
        The chat client to use for logging, by default None
    **kwargs
    """
    if url_or_file.startswith("http"):
        response = requests.get(url_or_file)
        response.raise_for_status()
        audio = response.content
        # create the file
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(audio)
        url_or_file = f.name

    response = openai.Audio.translate(
        url_or_file, model=model, prompt=prompt, 
        language=language, response_format='json', 
        **kwargs)

    return response.get("text")