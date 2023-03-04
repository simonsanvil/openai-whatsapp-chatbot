import inspect
import logging
from typing import Union

from twilio.rest import Client
from chat.clients import ChatClient
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Media:
    url: str
    content_type: str
    is_image: bool = field(init=False)
    is_audio: bool = field(init=False)
    is_video: bool = field(init=False)

    def __post_init__(self):
        self.__dict__['is_image'] = self.content_type.lower().startswith('image')
        self.__dict__['is_video'] = self.content_type.lower().startswith('video')
        self.__dict__['is_audio'] = self.content_type.lower().startswith('audio')

@dataclass
class TwilioWhatsAppMessage:
    body: str
    from_: str
    to: str
    media: Media = None

    def __post_init__(self) -> None:
        if not self.from_.startswith("whatsapp:"):
            self.from_ = f"whatsapp:{self.from_}"
        if not self.to.startswith("whatsapp:"):
            self.to = f"whatsapp:{self.to}"
    
    def send(self, client: Client):
        if self.media:
            return client.messages.create(
                from_=self.from_,
                to=self.to,
                media_url=self.media.url,
                body=self.body
            )
        else:
            return client.messages.create(
                from_=self.from_,
                to=self.to,
                body=self.body
            )
    
    async def send_async(self, client: Client):
        if self.media:
            return client.messages.create(
                from_=self.from_,
                to=self.to,
                media_url=self.media.url,
                body=self.body
            )
        else:
            return client.messages.create(
                from_=self.from_,
                to=self.to,
                body=self.body
            )


class TwilioWhatsAppClient(ChatClient):

    def __init__(
            self,
            account_sid: str = None,
            auth_token: str = None,
            from_number: str = None,
            client: Client = None,
            config: dict = None,
            **kwargs):
        if config is None:
            config = {}
        if client is None:
            assert account_sid is not None, "account_sid must be provided"
            assert auth_token is not None, "auth_token must be provided"
            client = Client(account_sid, auth_token, **kwargs.get("client_kwargs", {}))
        assert from_number is not None, "from_number must be provided"
        config.update(kwargs)
        config['client'] = client
        super().__init__(config)
        self.client = client
        self.config = config
        self.from_number = from_number
        self.logger = logging.getLogger("twilio_whatsapp")
        self.logger.setLevel(logging.INFO)
    
    def __getattr__(self, name):
        if name in self.config:
            return self.config[name]
        if name in self.client.__dict__:
            return self.client.__dict__[name]
        return super().__getattr__(name)

    def send_message(
        self, 
        message:Union[TwilioWhatsAppMessage, str], 
        to_number:str=None,
        media_url:str=None,
        media_type:str=None,
        on_failure:str=None, 
        **kwargs):
        """
        Send a WhatsApp message to a number.
        """
        if not isinstance(message, TwilioWhatsAppMessage):
            message = self.make_message(message, to_number, media_url, media_type)
        try:
            return message.send(self.client)
        except Exception as e:
            if on_failure is not None:
                if isinstance(on_failure, callable):
                    return on_failure(e, **kwargs)
                return on_failure
            else:
                self.on_failure(e, **kwargs)

    async def send_message_async(
        self, 
        message:Union[TwilioWhatsAppMessage, str], 
        to_number:str = None,
        media_url:str = None,
        media_type:str = None,
        ):
        """
        Send media to a WhatsApp number asynchronously.
        """
        if inspect.iscoroutine(message):
            message = await message
        if inspect.iscoroutine(media_url):
            media_url = await media_url
        if not isinstance(message, TwilioWhatsAppMessage):
            message = self.make_message(message, to_number, media_url, media_type)
        return await message.send_async(self.client)
    
    def make_message(self, message:str, to_number:str = None, media_url:str = None, media_type:str = None) -> TwilioWhatsAppMessage:
        """
        Make a TwilioWhatsAppMessage object.
        """
        if media_url is not None and media_type is not None:
            media = Media(url=media_url, content_type=media_type)
        else:
            media = None
        message = TwilioWhatsAppMessage(
            body=message, 
            from_=self.from_number,
            to=to_number,
            media=media)
        return message

    def parse_request_values(self, request_values:dict) -> TwilioWhatsAppMessage:
        """
        Parse the POST request values from the Twilio webhook
        and returns a TwilioWhatsAppMessage object.
        """
        msg_media = None
        if int(request_values.get("NumMedia")) > 0:
            media_url = request_values.get("MediaUrl0")
            media_type = request_values.get("MediaContentType0")
            msg_media = Media(url=media_url, content_type=media_type)
        message = TwilioWhatsAppMessage(
            body=request_values.get("Body"),
            from_=request_values.get("From"),
            to=request_values.get("To"),
            media=msg_media
        )
        # print(request_values, msg_media, message, sep="\n")
        return message

    def receive_message(self, **kwargs):
        raise NotImplementedError

    def get_user(self, **kwargs):
        raise NotImplementedError