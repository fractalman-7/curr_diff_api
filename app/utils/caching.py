import abc
import collections
import json
import typing as tp

import aioredis

LRU_KEYS_KEY = "KEYS"


class BaseCache(abc.ABC):
    async def init(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def get(self, key: str) -> tp.Optional[str | int | float | list | dict]:
        raise NotImplementedError

    async def put(self, key: str, value: str | int | float | list | dict) -> None:
        raise NotImplementedError


class BaseCacheStorage(abc.ABC):
    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def get(self, key: str) -> tp.Optional[str | int | float | list | dict]:
        raise NotImplementedError

    async def set(self, key: str, value: str | int | float | list | dict) -> None:
        raise NotImplementedError

    async def remove(self, key: str) -> None:
        raise NotImplementedError


class MemoryStorage(BaseCacheStorage):
    def __init__(self):
        self._data = {}

    async def get(self, key: str) -> tp.Optional[str | int | float | list | dict]:
        return self._data.get(key)

    async def set(self, key: str, value: str | int | float | list | dict) -> None:
        self._data[key] = value

    async def remove(self, key: str) -> None:
        self._data.pop(key)


class RedisStorage(BaseCacheStorage):
    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    async def get(self, key: str) -> tp.Optional[str | int | float | list | dict]:
        value = await self._redis.get(key)
        if value is None:
            return None
        return json.loads(
            value,
            parse_float=lambda x: x,
            parse_int=lambda x: x,  # Don't parse float and int
        )

    async def set(self, key: str, value: str | int | float | list | dict) -> None:
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)
        await self._redis.set(key, value)

    async def remove(self, key: str) -> None:
        await self._redis.delete(key)

    async def close(self) -> None:
        await self._redis.close()


class LRUCache(BaseCache):
    def __init__(
            self, capacity: int = 128, storage: BaseCacheStorage = MemoryStorage()
    ):
        self._storage = storage
        self._capacity = capacity
        self._keys = collections.deque()

    async def init(self) -> None:
        await self._storage.open()
        keys = await self._storage.get(LRU_KEYS_KEY)
        if keys is None:
            keys = []
        self._keys = collections.deque(keys)

    async def close(self) -> None:
        await self._storage.set(LRU_KEYS_KEY, list(self._keys))
        await self._storage.close()

    async def get(self, key: str) -> tp.Optional[str | int | float | list | dict]:
        value = await self._storage.get(key)
        if value is None:
            return None
        self._keys.remove(key)
        self._keys.append(key)
        return value

    async def put(self, key: str, value: str | int | float | list | dict) -> None:
        await self._storage.set(key, value)
        self._keys.append(key)
        if len(self._keys) > self._capacity:
            key = self._keys.popleft()
            await self._storage.remove(key)
