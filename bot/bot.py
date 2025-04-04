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
    _is_connected = False  # Track connection state

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
        time_diff = abs(time.time() - time.mktime(datetime.utcnow().timetuple()))
        if time_diff > 30:
            self.LOGGER(__name__).warning(f"System time is out of sync by {time_diff} seconds!")

    async def safe_start_client(self):
        """Handle client startup with proper connection management"""
        if self._is_connected:
            self.LOGGER(__name__).warning("Client is already connected")
            return True

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add initial delay to help with time sync
                if attempt > 0:
                    await asyncio.sleep(2 * attempt)
                
                await super().start()
                self._is_connected = True
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                if attempt == max_retries - 1:
                    self.LOGGER(__name__).error(f"Final connection attempt failed: {e}")
                    raise

                if "msg_id too low" in error_msg or "time sync" in error_msg:
                    wait_time = 5 * (attempt + 1)
                    self.LOGGER(__name__).warning(
                        f"Time sync issue (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time} seconds..."
                    )
                else:
                    wait_time = 3 * (attempt + 1)
                    self.LOGGER(__name__).warning(
                        f"Connection failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time} seconds... Error: {e}"
                    )
                
                await asyncio.sleep(wait_time)
        
        return False

    async def start(self):
        """Main startup routine"""
        await self.check_time_sync()
        
        try:
            if not await self.safe_start_client():
                raise ConnectionError("Failed to start client after retries")

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

        except Exception as e:
            self.LOGGER(__name__).error(f"Failed to start bot: {e}")
            raise

    async def stop(self, *args):
        if self._is_connected:
            await super().stop()
            self._is_connected = False
            self.LOGGER(__name__).info("NoPMsBot stopped. Bye.")