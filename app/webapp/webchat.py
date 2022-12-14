import requests, os
import html
import logging

from flask import Flask, request, render_template, url_for, jsonify
from pandas import to_datetime, to_timedelta

from openai_agent.agent import OpenAIAgent
from openai_agent.agent_utils import process_message_and_get_reply

from dotenv import find_dotenv, load_dotenv

logging.basicConfig()
logger = logging.getLogger("APP")
logger.setLevel(logging.DEBUG)
load_dotenv(find_dotenv())

app = Flask(__name__)
chat_agent = OpenAIAgent(
    engine="davinci-codex",
    agent_name=os.environ.get("AGENT_NAME"),
    chatter_name=os.environ.get("CHATTER_NAME", "HUMAN"),
)

# @app.route("/")
def index():
    print(os.getcwd())
    return render_template("docs.html")


# @app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get("Body", "")
    resp = MessagingResponse()
    msg = resp.message()
    reply = process_message_and_get_reply(chat_agent, incoming_msg, 120)
    msg.body(reply)
    return str(resp)


# @app.route('/chat/<string:msg>')
def chat(msg):
    if not chat_agent.is_conversation_active:
        chat_agent.start_conversation()
    logger.info("Previous conversation history: " + chat_agent.conversation)
    reply = process_message_and_get_reply(chat_agent, msg, 120)
    conversation = chat_agent.conversation  # chat_agent.make_chat_prompt(msg,False)
    conversation = conversation  # +reply
    conversation_html = conversation.replace(
        chat_agent.START_TEMPLATE, "<strong>" + chat_agent.START_TEMPLATE + "</strong>"
    ).replace("\n", "<br>")
    logger.debug("New conversation history in html: " + conversation_html)
    return render_template("chat_template.html", conversation=conversation_html)


# @app.route('/conversation')
def show_conversation():
    conversation = chat_agent.conversation
    conversation_html = conversation.replace(
        chat_agent.START_TEMPLATE, "<strong>" + chat_agent.START_TEMPLATE + "</strong>"
    ).replace("\n", "<br>")
    return render_template("chat_template.html", conversation=conversation_html)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    Function that receives a text message in the reponse of a POST request
    """
    if not chat_agent.is_conversation_active:
        chat_agent.start_conversation()
    data = request.get_json()
    logger.debug(str(data))
    if data is not None:
        if "message" not in data:
            return jsonify({"error": 'missing required "message" field'}), 400
        msg = data.pop("message")
        if "engine" in data:
            agent = OpenAIAgent(
                engine=data.pop("engine"),
                agent_name=os.environ.get("AGENT_NAME"),
                chatter_name=os.environ.get("CHATTER_NAME", "HUMAN"),
            )
        else:
            agent = chat_agent.copy()
        if "chatter_name" in data:
            chat_agent.set_chatter_name(data.pop("chatter_name"))
        if "agent_name" in data:
            chat_agent.set_agent_name(data.pop("agent_name"))
        data["max_tokens"] = data.pop("length", data.get("max_tokens", 120))
        if data:
            agent.set_agent_params(**data)
        reply = process_message_and_get_reply(agent, msg)
    else:
        reply = "I do not understand you!"
        return jsonify({"reply": reply})

    json_resp = {
        "agent_name": agent.agent_name,
        "engine": agent.engine,
        "message": msg,
        "reply": reply,
        "time": to_datetime("now").isoformat(),
    }

    return jsonify(json_resp)


@app.route("/api/completion", methods=["POST"])
def api_completion():
    data = request.get_json()
    logger.debug(str(data))
    if data:
        if "message" not in data and "prompt" not in data:
            return jsonify({"error": 'missing required "prompt" field'}), 400
        if "prompt" in data:
            prompt = data.pop("prompt")
        if "message" in data:
            prompt = data.pop("message")
        if "engine" in data:
            agent = OpenAIAgent(
                engine=data.pop("engine"),
                agent_name=os.environ.get("AGENT_NAME"),
                chatter_name=os.environ.get("CHATTER_NAME", "HUMAN"),
            )
        else:
            agent = chat_agent.copy()
        data["max_tokens"] = data.pop("length", data.get("max_tokens", 120))
        if data:
            agent.set_agent_params(**data)
        completion = agent.get_completion(prompt)
    else:
        return jsonify({"error": "missing json payload"}), 400

    json_resp = {
        "engine": agent.engine,
        "completion": prompt + completion.choices[0].text,
        "time": to_datetime("now").isoformat(),
    }

    return jsonify(json_resp)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
