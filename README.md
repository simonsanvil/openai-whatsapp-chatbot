OpenAI Chatbot
==============================

A web-based chatbot that uses OpenAI's famous transformer-based language models such as GTP3 and Codex to reply to incoming messages from whatsapp or via http.

Requires a valid key to OpenAI's API and access to their GTP-based engines (davinci, codex, ada, babbage, etc).

Installation
------
```bash
git clone https://github.com/simonsanvil/openai-whatsapp-chatbot
pip install -r requirements.txt
``` 

Requirements
-----------

-  python>=3.7
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

- Other environmental variables can be set to control the default parameters of the agent.

```bash
export MAX_TOKENS=[NUMBER OF MAX TOKENS IN EACH REPLY] #=150
export CONVERSATION_EXPIRES_MINS=[NUMBER OF MINUTES UNTIL A CONVERSATION IS ERASED FROM MEMORY] #=180
```
- It is also enough to have these variables in a [.env](https://github.com/laravel/laravel/blob/master/.env.example) file in the working directory where the app is running.


Running the app
---------
### Run from the command line:

```bash
#To start the application that works with whatsapp:
python3 -m app whatsapp-app
```

```bash
#To start the HTTP application:
python3 -m app webapp
```

### Run with Docker:

Alternatively the docker container will automatically install all the requirements and run the HTTP application.

```bash
# building the image
docker build -t openai_chatbot .

#running the container
#It is expected that you have all the required environmental variables in a .env file
docker run -p 8000:8000 openai_chatbot --env_file=.env
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

After following the instructions in the Twilio for Whatsapp Sandbox you should be able to join your sandbox and start chatting with the agent inmediately

<img src="https://i.imgur.com/1tD5o9h.jpeg" width="450"/>



--------