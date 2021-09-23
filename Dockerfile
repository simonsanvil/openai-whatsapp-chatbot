FROM python:3.8-buster
WORKDIR /usr/src/app

ARG openai_api_key
ENV OPENAI_API_KEY="${OPENAI_API_KEY}" 

ARG twillio_auth_token=""
ENV TWILLIO_AUTH_TOKEN="${TWILLIO_AUTH_TOKEN}"

ARG twillio_account_sid=""
ENV TWILLIO_ACCOUNT_SID="${TWILLIO_ACCOUNT_SID}"

ARG from_whatsapp_number=""
ENV FROM_WHATSAPP_NUMBER="${FROM_WHATSAPP_NUMBER}"

ARG to_whatsapp_number=""
ENV TO_WHATSAPP_NUMBER="${TO_WHATSAPP_NUMBER}"

ARG allowed_phone_numbers=""
ENV ALLOWED_PHONE_NUMBERS="${ALLOWED_PHONE_NUMBERS}"

ARG available_engines=""
ENV AVAILABLE_ENGINES="${AVAILABLE_ENGINES}" 

RUN apt-get update 
RUN python3 --version && pip3 --version

COPY /app .
COPY ./requirements.txt .en[v] ./
RUN pip3 install -r requirements.txt

EXPOSE 8000
EXPOSE 8001
ENTRYPOINT python3 -m app whatsapp-app