import os, logging
from chat.clients import ChatClient
import openai, requests

async def text_to_image(prompt: str, *, as_url=True, **kwargs):
    """Generate an image asychronously given the prompt"""
    logging.debug(
        f"Querying OpenAI's Image API 'DALL-E' with prompt '{prompt}'"
    )
    creation_params = dict(n=1, size="1024x1024")
    creation_params.update(kwargs)
    # create a partial function to send the image with the given parameters
    response = openai.Image.create(
        prompt=prompt,
        **creation_params)
    data = response.get("data")
    if data is None:
        return None
    image_url = data[0].get("url")
    if image_url is None:
        return None
    if as_url:
        return image_url
    else:
        return requests.get(image_url).content