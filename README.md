OpenAI Chatbot
==============================

A chatbot that uses the OpenAI API to leverage the power of their famous transformer-based language models such as GTP3 and Codex to reply to incoming messages from whatsapp or via http

Requires a valid key to OpenAI's API and access to their GTP (davinci, ada, babbage) or Codex engines.

Requirements
-----------
- requires python>=3.7

```bash
git clone https://github.com/simonsanvil/openai-whatsapp-chatbot
pip install -r requirements.txt
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

### Run with Docker:

```bash
docker run container
```


--------