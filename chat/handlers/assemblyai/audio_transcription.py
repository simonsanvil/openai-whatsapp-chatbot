"""Use AssemblyAI's API for audio transcription"""

import os, time, logging
import requests

supported_language_codes = { # https://www.assemblyai.com/docs/#supported-languages
    'en': 'en',
    'english': 'en',
    'en-us': 'en_us',
    'en_us': 'en_us',
    'en-gb': 'en_gb',
    'en_gb': 'en_gb',
    'es': 'es',
    'spanish': 'es',
    'fr': 'fr',
    'french': 'fr',
    'de': 'de',
    'german': 'de',
    'it': 'it',
    'italian': 'it',
    'pt': 'pt',
    'portuguese': 'pt',
    'nl': 'nl',
    'dutch': 'nl',
    'ja': 'ja',
    'japanese': 'ja',
    'hi': 'hi',
    'hindi': 'hi',
}

def transcribe_audio(media_url, *, chat=None, language_detection:bool=True, language_code=None, api_key=None, as_json:bool=False):
    if chat is not None:
        logger = chat.logger
    else:
        logger = logging.getLogger(__name__)
    now = time.time()
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {
        "authorization": os.environ.get('ASSEMBLYAI_API_KEY') if api_key is None else api_key,
        "content-type": "application/json"
    }
    data = dict(audio_url=media_url, language_detection=language_detection)
    if language_code is not None:
        data['language_code'] = supported_language_codes.get(language_code, 'en')
        data['language_detection'] = False
    logger.info(f"Attempting to transcribe audio with {data=}")
    response = requests.post(endpoint, json=data, headers=headers)
    response.raise_for_status()
    transcription_id = response.json()['id']
    try:
        transcription_res = _wait_for_transcription(transcription_id, headers, logger=logger)
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error getting transcription {transcription_id}: {e} with request data: {data}")
        raise e
    except ValueError as e:
        logger.error(e)
        return None

    transcription_res.pop('words', None)
    logger.info(f"Transcription took {time.time() - now:.2f} seconds")
    logger.info(f"Transcription data:\n{transcription_res}")
    if as_json:
        return transcription_res
    return transcription_res['text']

def _wait_for_transcription(transcription_id:str, headers:dict, timeout=30, logger=None):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"
    time_now = time.time()
    response = requests.get(endpoint, headers=headers)
    while (status := response.json()['status']).lower() != 'completed':
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e
        if time.time() - time_now > 30: # 30 second timeout
            raise ValueError(f"Timed out waiting for transcription to complete. Status: {status}")
    return response.json()