FROM python:3.8-buster
WORKDIR /usr/src/app

RUN apt-get update 
RUN python3 --version && pip3 --version

# ADD openai-chatbot/ ./openai-chatbot
COPY ./requirements.txt .en[v] ./
RUN pip3 install -r requirements.txt
ADD /chat ./chat
ADD /app ./app

EXPOSE 8000
WORKDIR /usr/src/app
ENTRYPOINT python3 -m app whatsapp

# docker run -it --rm -v $(pwd)/data:/usr/src/app/data -p 5000:5000 --env-file .env --name whatsapp-chatbot whatsapp-chatbot
