from typing import Union, Tuple, List

import openai
from chat.clients import ChatClient

def edit_text(
    text:str, 
    prompt:str, 
    chat: ChatClient = None, 
    model:str = 'text-davinci-edit-001',
    return_index:bool = False,
    **kwargs
) -> Union[str, Tuple[str, int]]:
    """
    Returns a completion from OpenAI's Edit API.

    Parameters
    ----------
    text : str
        The text to edit.
    prompt : str
        The instruction prompt to use for editing.
    chat : ChatClient, optional
        The chat client to use for logging, by default None
    model : str, optional
        The model to use for editing, by default 'text-davinci-edit-001'
    **kwargs
        Additional keyword arguments to pass to the Completion API.
        See https://platform.openai.com/docs/api-reference/edits/create for a list of
        valid parameters.
    """
    if chat:
        chat.logger.info(f"Text edit with prompt '{prompt}'")
    response = openai.Edit.create(input=text, instruction=prompt, model=model, **kwargs)
    if chat:
        chat.log("OpenAI", response.get("text"))
    choice = response.get("choices",[{}])[0]
    edited_text = choice.get("text")
    edited_index = choice.get("index")
    if return_index:
        return edited_text, edited_index
    new_text = text[:edited_index] + edited_text + text[edited_index+len(edited_text):]
    return new_text

def edit_code(
    code:str, 
    prompt:str, 
    chat: ChatClient = None, 
    model:str = 'code-davinci-edit-001',
    return_index:bool = False,
    **kwargs
) -> Union[str, Tuple[str, int]]:
    """
    Returns a completion from OpenAI's Edit API.

    Parameters
    ----------
    code : str
        The code to edit.
    prompt : str
        The instruction prompt to use for editing.
    chat : ChatClient, optional
        The chat client to use for logging, by default None
    model : str, optional
        The model to use for editing, by default 'code-davinci-edit-001'
    **kwargs
        Additional keyword arguments to pass to the Completion API.
        See https://platform.openai.com/docs/api-reference/edits/create for a list of
        valid parameters.
    """
    return edit_text(code, prompt, chat, model, return_index, **kwargs)