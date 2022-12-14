from dataclasses import dataclass
from apscheduler.schedulers.background import BackgroundScheduler

from openai_agent import OpenAIAgent


@dataclass
class ChatManager:
    agent: OpenAIAgent
    scheduler: BackgroundScheduler
    timer_expire_seconds: int = 60 * 60 * 3  # 3 hours
    num_images_generated: int = 0
    image_captioning: bool = True
    voice_messages: bool = True
    voice_reply: bool = False

    @property
    def num_messages(self):
        return len(self.agent)

    def __len__(self):
        return len(self.agent)


@dataclass
class Sender:
    phone_number: str
    name: str
    country: str = None
    max_image_generations: int = 1
    max_messages: int = 50
