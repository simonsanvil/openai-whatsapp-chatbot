
class ChatClient:

    def __init__(self, config: dict):
        self.config = config

    def send_message(self, message: str, **kwargs):
        raise NotImplementedError

    def receive_message(self, **kwargs):
        raise NotImplementedError

    def get_user(self, **kwargs):
        raise NotImplementedError

    def on_failure(self, exception: Exception, **kwargs):
        raise exception