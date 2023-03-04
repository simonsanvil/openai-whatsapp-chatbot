from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Union
from enum import Enum

from chat.clients.twilio.twilio_whatsapp import TwilioWhatsAppClient

@dataclass
class User:
    phone_number: str
    name: str = None
    country: str = None
    max_messages_per_session: int = float("inf")
    image_generation: bool = True
    max_image_generations: int = float("inf")
    voice_transcription: bool = True
    transcription_language: str = None #"en-US"
    language: str = None #"en"
    timezone: str = None #"UTC"
    chat_model: str = None # use default chat model
    completion_model: str = None # use default completion model
    chat_system_message: str = None # use default chat system message

class Role(Enum):
    '''Roles of the chat'''
    SYSTEM = 'system'
    CLIENT = 'system'
    ASSISTANT = 'assistant'
    AGENT = 'assistant'
    USER = 'user'
    PERSON = 'user'

class MediaTypes(Enum):
    '''Media types'''
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'

@dataclass
class Media:
    url: str = None
    content: Union[str, bytes] = None
    content_type: Union[str, MediaTypes] = None
    caption: str = None

    def __post_init__(self):
        if isinstance(self.content_type, str):
            if self.content_type.upper() in MediaTypes.__members__:
                self.content_type = MediaTypes[self.content_type.upper()]
            else:
                raise ValueError(f"Invalid media type: {self.content_type}")

@dataclass
class Message:
    to: User
    role: Union[Role, str]
    from_: User = None
    text: str = None
    media: Media = None
    sent_at: datetime = None

    def __post_init__(self):
        if self.sent_at is None:
            self.sent_at = datetime.now()
        if isinstance(self.sent_at, str):
            self.sent_at = datetime.fromisoformat(self.sent_at)
        if not isinstance(self.role, Role):
            if self.role.upper() in Role.__members__:
                self.role = Role[self.role.upper()]
            else:
                raise ValueError(f"Invalid role: {self.role}")
        
    def send(self, client:TwilioWhatsAppClient, from_: User = None):
        if self.media is not None:
            media_url = self.media.url
            media_type = self.media.content_type.value
        else:
            media_url, media_type = None, None
        msg = client.make_message(self.text, to_number=self.to.phone_number, media_url=media_url, media_type=media_type)
        return client.send_message(msg)
    
@dataclass
class ChatSession:
    user: User
    start_time: datetime = None
    end_time: datetime = None
    messages: List[Message] = field(default_factory=list)
    system_message: str = None
    model: str = "gpt-3.5-turbo"
    time_to_expire_seconds: int = 60 * 60 * 3  # 3 hours
    caption_images: bool = True

    @property
    def end_conversation_phrases(self):
        return [
            "bye",
            "goodbye",
            "see you later",
            "see you",
            "talk to you later",
            "talk to you",
            "later",
            "bye bye",
            "quit",
            "exit",
            "restart conversation",
            "[restart]",
        ]

    @property
    def goodbye_message(self):
        return Message(
            text="Goodbye {user}! I'll be here if you need me.",
            to=self.user,
            role=Role.ASSISTANT,
        )