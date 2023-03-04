from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Union, Callable
# from apscheduler.schedulers.background import BackgroundScheduler

managers = {}


@dataclass
class OpenAIChatManager:
    sender: "Sender"
    model: str = "gpt-3.5-turbo"
    agent_name: str = None
    start_system_message: Union[str, Callable] = None
    messages: list = field(default_factory=list)
    message_info: list = field(default_factory=list)
    num_images_generated: int = 0
    max_image_generations: int = float("inf")
    allow_images: bool = True
    voice_transcription: bool = True
    transcription_language: str = None # automatically detect
    language: str = "english"
    # scheduler: BackgroundScheduler = None
    conversation_expire_seconds: int = 60 * 60 * 3  # 3 hours
    caption_images: bool = True
    goodbye_message: str = "Goodbye {user}! I'll be here if you need me."
    logger: logging.Logger = None
    
    end_conversation_phrases = [
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

    def __post_init__(self):
        self.add_message(self.start_system_message, role="system")
        if self.logger is None:
            self.logger = logging.getLogger(__name__)

    @classmethod
    def get_or_create(cls, sender: "Sender", model: str = "gpt-3.5-turbo", **kwargs):
        if sender.phone_number not in managers:
            managers[sender.phone_number] = cls(sender, model)
        for k, v in kwargs.items():
            setattr(managers[sender.phone_number], k, v)
        return managers[sender.phone_number]

    def save(self):
        managers[self.sender.phone_number] = self

    def get_messages_from(self, role: str):
        return [msg for msg in self.messages if msg["role"] == role]

    def add_message(self, message: str, role: str = "user"):
        msg = self.make_message(message, role)
        self.messages.append(msg)
        msg_info = {**msg, "timestamp": datetime.now().isoformat()}
        self.message_info.append(msg_info)

    def make_message(self, message: str, role: str = "user"):
        msg = {
            "role": role,
            "content": message,
        }
        return msg

    def start_or_restart_timer(self, callback: callable = None):
        if callback is None:
            callback = self.restart_conversation
        # if self.scheduler.running:
        #     self.restart_scheduler()
        # else:
        #     self.start_scheduler(callback)

    def restart_conversation(self):
        """Restarts conversation"""
        self.messages = []
        self.num_images_generated = 0
        sys_msg = (
            self.start_system_message()
            if callable(self.start_system_message)
            else self.start_system_message
        )
        sys_msg = sys_msg.format(sender=self.sender)
        self.add_message(sys_msg, role="system")
        # self.scheduler.pause()
        del managers[self.sender.phone_number]

    def get_conversation(self):
        msg_template = "{role}: {content}"
        return "\n".join(
            [
                msg_template.format(role=msg["role"].upper(), content=msg["content"])
                for msg in self.messages
            ]
        )

    def __len__(self):
        return len(self.messages)

    def __getitem__(self, index):
        return self.messages[index]

    def __delitem__(self, index):
        del self.messages[index]


@dataclass
class Sender:
    phone_number: str
    name: str
    country: str = None
    max_image_generations: int = 1
    max_messages: int = 50
    voice_transcription: bool = True
    transcription_language: str = "en-US"
