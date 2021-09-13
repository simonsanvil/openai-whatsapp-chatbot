OpenAI Chatbot
==============================

A chatbot that uses the OpenAI API to leverage the power of their famous transformer-based language models such as GTP3 and Codex to reply to incoming messages from whatsapp or via http

Requires a valid key to OpenAI's API and access to their GTP (davinci, ada, babbage) or Codex engines.

Installation
------
```bash
git clone https://github.com/simonsanvil/openai-whatsapp-chatbot
pip install -r requirements.txt
``` 

Requirements
-----------


-  python>=3.7
- Requires to create a [Twillio account](https://www.twilio.com/) and [setup a Twilio whatsapp messages sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn?frameUrl=%2Fconsole%2Fsms%2Fwhatsapp%2Flearn%3Fx-target-region%3Dus1) setting the */whatsapp/receive* endpoint of this app as its callback url when a message comes in and the */whatsapp/status* as its status callback url. (Just follow Twillio's tutorial)
- Additionally this app is expected to have the following environmental variables set in the environement where the web app is running

```bash
OPENAI_API_KEY=[ACCESS KEY TO OPENAI's API]
TWILLIO_AUTH_TOKEN=[YOUR TWILLIO AUTH TOKEN]
TWILLIO_ACCOUNT_SID=[YOUR TWILLIO ACCOUNT SID]
FROM_WHATSAPP_NUMBER=[YOUR ASSIGNED TWILLIO WHATSAPP NUMBER]
```


Usage
---------
### Run from the command line:

To start the application that works with whatsapp: (requires a Twillio auth key)

```bash
python3 -m app whatsapp-app
```

To start the HTTP application:

```bash
python3 -m app webapp
```

### ~ Run with Docker:

```bash
#TODO
```


--------