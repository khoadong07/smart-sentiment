from aiocache import Cache
from app.settings import Settings

settings = Settings()


cache = Cache(Cache.REDIS, endpoint=settings.REDIS_HOST, port=6379, namespace="buzz-cache", ttl=3600)
