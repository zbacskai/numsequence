import asyncio
from datetime import datetime, timedelta


async def maintain_sessions(session_storage):
    while True:
        current_time = datetime.now()
        for expiry_date, key in session_storage.expiries:
            if current_time >= expiry_date:
                print(f"Purging client info for: {key}")
                del session_storage.obj_store[key]

        session_storage.expiries = [
            x for x in session_storage.expiries if x[0] > current_time
        ]

        await asyncio.sleep(1)


class SessionStorage:
    def __init__(self):
        loop = asyncio.get_running_loop()
        self.obj_store = {}
        self.expiries = []
        self._task = loop.create_task(maintain_sessions(self))

    def set(self, key, in_object, exp=-1):
        if exp != 0:
            self.obj_store[key] = in_object
        if exp >= 0:
            expiry_date = datetime.now() + timedelta(seconds=exp)
            self.expiries.append(
                (
                    expiry_date,
                    key,
                )
            )

    def get(self, key):
        return self.obj_store.get(key)

    def __del__(self):
        self._task.cancel()
