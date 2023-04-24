import os
import redis
from abc import ABC, abstractmethod
from typing import Any, Optional
from hunting_hawk.scrape.scrape import Move

from pydantic.json import pydantic_encoder
from json import dumps


class Cache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, val: str) -> Optional[bool]:
        pass

    @abstractmethod
    def get_list(self, key: str) -> list[str]:
        pass

    @abstractmethod
    def set_list(self, key: str, vals: list[str]) -> list[Any]:
        pass

    @abstractmethod
    def set_model(self, key: str, val: list[Move]) -> Optional[bool]:
        pass


class RedisCache(Cache):
    expiry: int = 60 * 60 * 24 * 7

    def __init__(self, host: str, port: int, db: int) -> None:
        self.client = redis.StrictRedis(host=host, port=port, db=db)

    def get(self, key: str) -> Optional[str]:
        if val := self.client.get(key):
            return val.decode("utf-8")
        return None

    def set(self, key: str, val: str) -> Optional[bool]:
        return self.client.set(key, val, ex=self.expiry)

    def get_list(self, key: str) -> list[str]:
        return [b.decode("utf-8") for b in self.client.lrange(key, 0, -1)]

    def set_list(self, key: str, vals: list[str]) -> list[Any]:
        pipe = self.client.pipeline()
        pipe.delete(key)
        pipe.rpush(key, *vals)
        pipe.expire(key, self.expiry)
        return pipe.execute()

    def set_model(self, key: str, val: list[Move]) -> Optional[bool]:
        json_vals = dumps(val, indent=2, default=pydantic_encoder)
        return self.client.set(key, json_vals, ex=self.expiry)


class DictCache(Cache):
    _data: dict[str, Any] = {}

    def get(self, key: str) -> Optional[str]:
        if key not in self._data:
            return None

        val = self._data[key]
        if type(val) is str:
            return val
        raise

    def set(self, key: str, val: str) -> Optional[bool]:
        self._data[key] = val
        return True

    def get_list(self, key: str) -> list[str]:
        if key not in self._data:
            return []

        val = self._data[key]
        match val:
            case list():
                return val
            case _:
                raise

    def set_list(self, key: str, val: list[str]) -> list[Any]:
        self._data[key] = val
        return val

    def set_model(self, key: str, val: list[Move]) -> Optional[bool]:
        json_vals = dumps(val, indent=2, default=pydantic_encoder)
        self._data[key] = json_vals
        return True


class FallbackCache(Cache):
    selected_cache: Cache

    def __init__(self) -> None:
        self.selected_cache = DictCache()
        try:
            host = os.environ.get("REDIS_HOST", "localhost")
            port = int(os.environ.get("REDIS_PORT", 6379))
            db = int(os.environ.get("REDIS_DB", 0))
            self.redis_cache = RedisCache(host, port, db)
            if self.redis_cache.client.ping():
                self.selected_cache = self.redis_cache
        except (ValueError, redis.exceptions.ConnectionError):
            pass

    def get(self, key: str) -> Optional[str]:
        return self.selected_cache.get(key)

    def set(self, key: str, val: str) -> Optional[bool]:
        return self.selected_cache.set(key, val)

    def get_list(self, key: str) -> list[str]:
        return self.selected_cache.get_list(key)

    def set_list(self, key: str, val: list[str]) -> list[Any]:
        return self.selected_cache.set_list(key, val)

    def set_model(self, key: str, val: list[Move]) -> Optional[bool]:
        return self.selected_cache.set_model(key, val)