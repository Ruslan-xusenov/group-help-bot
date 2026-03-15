import time
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, slow_mode_delay: float = 1.5):
        self.delay = slow_mode_delay
        self.users: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()

        if user_id in self.users:
            last_time = self.users[user_id]
            if now - last_time < self.delay:
                # Silently ignore or you could answer "Too fast"
                return
        
        self.users[user_id] = now
        return await handler(event, data)
