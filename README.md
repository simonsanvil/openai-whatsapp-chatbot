WhatApp OpenAI-API Chatbot
==============================

[![Build and deploy Python app to Azure Web App - openai-chatbot](https://github.com/simonsanvil/openai-whatsapp-chatbot/actions/workflows/master_openai-chatbot.yml/badge.svg)](https://github.com/simonsanvil/openai-whatsapp-chatbot/actions/workflows/master_openai-chatbot.yml)

A chatbot that uses OpenAI's API to reply to incoming text and voice messages from WhatsApp with their GPT3-based language models (Davinci, Ada, Babbage, ...) and to generate images with [DALL-E 2](https://openai.com/dall-e-2/).

Requires a valid key to [OpenAI's API](https://openai.com/api/).

![](https://i.imgur.com/59v9gFH.png) | ![](https://i.imgur.com/xCJrOZz.png) | ![](https://i.imgur.com/dfluSaY.png)
:------------:|:-----------:|:-----------:
   |  | 



    
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

Setup and Configuration
--------------------

You need to set the OpenAI API key as an environmental variables or add it to a [.env](https://github.com/laravel/laravel/blob/master/.env.example) file in the working directory where the app will be running:
```bash
export OPENAI_API_KEY=[YOUR OPENAI API ACCESS KEY]
```

### To run the Whatsapp chatbot:
- Have a [Twillio account](https://www.twilio.com/) and setup a [Twilio for Whatsapp messages sandbox](https://www.twilio.com/docs/whatsapp/sandbox) with the `/whatsapp/receive` endpoint of this app as its callback url and `/whatsapp/status` as its status callback url (follow Twillio's tutorial for instructions about how this is done, should only take a few minutes). 
- Set the following environmental variables: (or add them to the same .env file as the one with the api key).
```bash
export TWILLIO_AUTH_TOKEN=[YOUR TWILIO AUTH TOKEN]
export TWILLIO_ACCOUNT_SID=[YOUR TWILIO ACCOUNT SID]
export FROM_WHATSAPP_NUMBER=[YOUR ASSIGNED TWILIO WHATSAPP NUMBER] #+14155238886
```

The image below shows which boxes you need to fill in when configuring your Twillio Sandbox for Whatsapp:

![](https://i.imgur.com/29vUDK0.png)


### Additional config:

- Other environmental variables can be set to control the default parameters of the agent (see [agent.py](/gtp-chatbot/gtp_agent/agent.py) for more details), control configurations of the app, or activate specific features:

```bash
export MAX_TOKENS=[NUMBER OF MAX TOKENS IN EACH REPLY]
export CONVERSATION_EXPIRES_MINS=[N MINUTES UNTIL A CONVERSATION IS ERASED FROM MEMORY]
export ALLOWED_PHONE_NUMBERS=[+1234567890,+1987654321] # Default is any number
export START_TEMPLATE=[PATH TO A FILE WITH A TEMPLATE FOR THE START OF A CONVERSATION] #data/start_template.txt
export ASSEMBLYAI_API_KEY=[YOUR ASSEMBLY-AI API KEY]
```
- It is also enough to have these variables in a [.env](https://github.com/laravel/laravel/blob/master/.env.example) file in the working directory where the app is running.

The `ASSEMBLYAI_API_KEY` environmental variable is to use [AssemblyAI's API](https://www.assemblyai.com/) to parse and transcribe the audio of incoming voice messages so that the agent can reply to them. If you don't need or want this, you can ignore that variable.

Running the app
---------
### Run from the command line:

```bash
# (Use --help to see all the options):
python3 -m app.whatsapp
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

After following the instructions in the [Twilio Sandbox for Whatsapp Tutorial](https://www.twilio.com/docs/whatsapp/sandbox) you should be able to join your sandbox and start chatting with the agent inmediately

<img src="https://i.imgur.com/EdYxOWe.jpg" width="450"/>


--------
