import os

from dotenv import load_dotenv

load_dotenv()


class ConfigProvider:
    def __init__(self):
        self.openai_key = os.getenv("OPENAIKEY")

    def get_openai_key(self):
        return self.openai_key

    def get_redis_url(self):
        redishost = os.getenv("REDISHOST", "redis")
        redisport = int(os.getenv("REDISPORT", 6379))
        redisuser = os.getenv("REDISUSER", "")
        redispassword = os.getenv("REDISPASSWORD", "")
        # Construct the Redis URL
        if redisuser and redispassword:
            redis_url = f"redis://{redisuser}:{redispassword}@{redishost}:{redisport}/0"
        else:
            redis_url = f"redis://{redishost}:{redisport}/0"
        return redis_url


config_provider = ConfigProvider()