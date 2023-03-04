import logging
import re
from chat.clients import ChatClient
from typing import Tuple

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

    ).group(1)
    new_msg = re.sub(r"\[img:\s*\"(.*)\"\]", "", msg, flags=re.IGNORECASE)
    logging.info(f"Image generation prompt: '{img_generation_prompt}'")
    return new_msg, img_generation_prompt