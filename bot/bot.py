from pyrogram import Client, __version__
from pyrogram.errors import BadRequest
from bot import (
    API_HASH,
    APP_ID,
    AUTH_CHANNEL,
    DEFAULT_START_TEXT,
    LOGGER,
    START_COMMAND,
    START_OTHER_USERS_TEXT,
    TG_BOT_TOKEN,
    TG_BOT_WORKERS
)
import time
import asyncio
from datetime import datetime

class Bot(Client):
    """ modded client for NoPMsBot """
    commandi = {}

    def __init__(self):
        super().__init__(
            "NoPMsBot",
            api_hash=API_HASH,
            api_id=APP_ID,
            bot_token=TG_BOT_TOKEN,
            plugins={"root": "bot/plugins"},
            workers=TG_BOT_WORKERS
        )
        self.LOGGER = LOGGER

    async def check_time_sync(self):
        """Verify system time is roughly correct"""
        self.LOGGER(__name__).info(f"System time: {datetime.utcnow()}")
        if abs(time.time() - time.mktime(datetime.utcnow().timetuple())) > 30:
            self.LOGGER(__name__).warning("System time might be out of sync!")

    async def start(self):
        # First verify time sync
        await self.check_time_sync()

        # Connection retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await super().start()
                break
            except Exception as e:
                if "msg_id too low" in str(e) or "time has to be synchronized" in str(e):
                    # Time sync error
                    if attempt == max_retries - 1:
                        raise
                    wait_time = 2 * (attempt + 1)
                    self.LOGGER(__name__).warning(
                        f"Time sync error (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Other connection error
                    if attempt == max_retries - 1:
                        raise
                    wait_time = 5 * (attempt + 1)
                    self.LOGGER(__name__).warning(
                        f"Connection failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time} seconds... Error: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)

        # Bot setup
        usr_bot_me = await self.get_me()
        self.set_parse_mode("html")
        
        try:
            check_m = await self.get_messages(
                chat_id=AUTH_CHANNEL,
                message_ids=START_OTHER_USERS_TEXT,
                replies=0
            )
            self.commandi[START_COMMAND] = check_m.text.html if check_m else DEFAULT_START_TEXT
        except BadRequest as e:
            self.LOGGER(__name__).warning(f"Failed to get start message: {e}")
            self.commandi[START_COMMAND] = DEFAULT_START_TEXT

        self.LOGGER(__name__).info(
            f"@{usr_bot_me.username} based on Pyrogram v{__version__} started successfully."
        )

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("NoPMsBot stopped. Bye.")