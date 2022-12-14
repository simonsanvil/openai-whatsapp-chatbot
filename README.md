OpenAI Chatbot
==============================

[![Build and deploy Python app to Azure Web App - openai-chatbot](https://github.com/simonsanvil/openai-whatsapp-chatbot/actions/workflows/master_openai-chatbot.yml/badge.svg)](https://github.com/simonsanvil/openai-whatsapp-chatbot/actions/workflows/master_openai-chatbot.yml)

A chatbot that uses OpenAI's famous transformer-based language model GPT3 (Davinci, Codex) to reply to incoming text and voice messages from WhatsApp and to generate images with OpenAI's [DALL-E](https://openai.com/dall-e-2/).

Requires a valid key to OpenAI's API and access to their GPT-based engines (davinci, instruct, code, ...).
    
Installation
------
```bash
git clone https://github.com/simonsanvil/openai-whatsapp-chatbot
pip install -r requirements.txt
``` 

Requirements
-----------

-  python>=3.8
- A valid [OpenAI API](https://beta.openai.com/) key

Configuration
--------------------

You need to set the OpenAI API key as an environmental variables or add it to a [.env](https://github.com/laravel/laravel/blob/master/.env.example) file in the working directory where the app will be running:
```bash
export OPENAI_API_KEY=[YOUR OPENAI API ACCESS KEY]
```

### To run the Whatsapp chatbot:
- Have a [Twillio account](https://www.twilio.com/) and [setup a Twilio whatsapp messages sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn?frameUrl=%2Fconsole%2Fsms%2Fwhatsapp%2Flearn%3Fx-target-region%3Dus1) with the */whatsapp/receive* endpoint of this app as its callback url when a message comes in and the */whatsapp/status* as its status callback url. (Follow Twillio's tutorial)
- Set the following environmental variables: (or add them to the same .env file as the one with the api key).
```bash
export TWILLIO_AUTH_TOKEN=[YOUR TWILIO AUTH TOKEN]
export TWILLIO_ACCOUNT_SID=[YOUR TWILIO ACCOUNT SID]
export FROM_WHATSAPP_NUMBER=[YOUR ASSIGNED TWILIO WHATSAPP NUMBER]
```

### Additional config:

- Other environmental variables can be set to control the default parameters of the agent (see [agent.py](/gtp-chatbot/gtp_agent/agent.py) for more details), control configurations of the app, or activate features of the app:

```bash
export MAX_TOKENS=[NUMBER OF MAX TOKENS IN EACH REPLY]
export CONVERSATION_EXPIRES_MINS=[N MINUTES UNTIL A CONVERSATION IS ERASED FROM MEMORY]
export ALLOWED_PHONE_NUMBERS=[+1234567890,+1987654321] # Default is any number
export START_TEMPLATE=[PATH TO A FILE WITH A TEMPLATE FOR THE START OF A CONVERSATION]
```
- It is also enough to have these variables in a [.env](https://github.com/laravel/laravel/blob/master/.env.example) file in the working directory where the app is running.

You an also set the `ASSEMBLYAI_API_KEY` environmental variable to use [AssemblyAI's API](https://www.assemblyai.com/) to parse and transcribe the audio of incoming voice messages so that the agent can reply to them.

Running the app
---------
### Run from the command line:

```bash
#To start the application that works with whatsapp
# (Use --help to see all the options):
python3 -m app.whatsapp
```

```bash
#To start the HTTP application:
python3 -m app.webapp
```

### Run with Docker:

Alternatively the docker container will automatically install all the requirements and run the whatsapp application.

```bash
# building the image
docker build -t openai-ws-chatbot .

#running the container
#It is expected that you have all the required environmental variables in a .env file
docker run -p 5000:5000 openai-ws-chatbot --env_file=.env
```

Usage
-------
### HTTP Application


You can converse with the agent by making a `POST` request to the `api/chat` endpoint of the application with your "message" in its json payload.

**Example:**


```http
### Obtaining a reply from the davinci engine to a custom message
POST /api/chat HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "message": "Hey",
    "engine": "davinci",
    "max_tokens": 100
}
```

JSON response: 

```json
{
  "agent_name": "DAVINCI",
  "engine": "davinci",
  "message": "Hey",
  "reply": "Hello and thank you, Human. I will gladly fill in your request. Please let me know if you need anything else.",
  "time": "2021-09-25T20:28:44.100765"
}
```

You can also obtain direct completions from an specified agent by making a `POST` request to the `api/completion` endpoint of the application specifying your "prompt" key in its json payload.

**Example:**

```http
### Obtain direct completions from an specified agent
POST /api/completion HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "message": "import pandas as pd\npd.read",
    "engine": "davinci-codex",
    "max_tokens": 20
}
```

JSON response: 

```json
{
  "completion": "import pandas as pd\npd.read_csv('../../data/raw/raw_data.csv')\n",
  "engine": "davinci-codex",
  "time": "2021-09-25T20:36:00.412107"
}
```

### Whatsapp Chatbot

After following the instructions in the Twilio for Whatsapp Sandbox Tutorial you should be able to join your sandbox and start chatting with the agent inmediately

<img src="https://i.imgur.com/EdYxOWe.jpg" width="450"/>



--------
