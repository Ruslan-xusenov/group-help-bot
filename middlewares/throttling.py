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
        
        # Periodic cleanup (1% chance per call to keep memory clean)
        if len(self.users) > 1000 and time.time() % 100 < 1:
            self._cleanup()
        
        return await handler(event, data)

    def _cleanup(self):
        now = time.time()
        # Remove users who haven't messaged in a while (10x the delay)
        expired = [uid for uid, ltime in self.users.items() if now - ltime > self.delay * 10]
        for uid in expired:
            del self.users[uid]
