OpenAI Chatbot
==============================

A web-based chatbot that uses the OpenAI API to leverage the power of their famous transformer-based language models such as GTP3 and Codex to reply to incoming messages from whatsapp or via http

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

You need to set the OpenAI key as an environmental variables or add it to a [.env](https://github.com/laravel/laravel/blob/master/.env.example) file.:
```bash
export OPENAI_API_KEY=[YOUR OPENAI API ACCESS KEY]
```

### To run the Whatsapp chatbot (optional):
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
export CONVERSATION_EXPIRES_MINS=[NUMBER OF MINUTES UNTIL A CONVERSATION IS ERASED FROM MEMORY] #=60*3
```
- It is also enough to have these variables in the [.env](https://github.com/laravel/laravel/blob/master/.env.example) file in the working directory where the app is running.


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

```bash
# building the image
docker build -t openai_chatbot .

#running the container
#It is expected that you have all the required environmental variables in a .env file
docker run -p 8000:8000 openai_chatbot --env_file=.env
```


--------