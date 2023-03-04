from typing import Union
import openai

def text_moderation(
    text, 
    chat=None, 
    model="text-moderation-latest", 
    return_flagged=False,
    **kwargs
) -> Union[bool, dict]:
    """
    Returns a completion from OpenAI's Moderation API.

    Parameters
    ----------
    text : str
        The text to moderate.
    chat : ChatClient, optional
        The chat client to use for logging, by default None
    model : str, optional
        The model to use for moderation, by default 'davinci'
    return_flagged : bool, optional
        Whether to return if the text was flagged as inappropriate.
        Otherwise, the full results (with categories and scores) are returned.
        By default False
    **kwargs
        Additional keyword arguments to pass to the Moderation API.
        See https://platform.openai.com/docs/api-reference/moderations for a list of
        valid parameters.
    """
    if chat:
        chat.logger.info(f"Text moderation with model '{model}'")
    response = openai.Moderation.create(input=text, model=model, **kwargs)
    result = response.get("results", [{}])[0]
    if return_flagged:
        return result.get("flagged")
    return result