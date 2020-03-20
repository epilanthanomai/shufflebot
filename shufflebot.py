import logging
import os

from discord import Client

logger = logging.getLogger("shufflebot")


class BotBase(Client):
    DEFAULT_COMMAND_PREFIX = "+"

    def __init__(self, *args, **kwargs):
        self.command_prefix = kwargs.pop("command_prefix", self.DEFAULT_COMMAND_PREFIX)
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not message.content.startswith(self.command_prefix):
            return

        unprefixed = message.content[len(self.command_prefix) :]
        command_name, _, rest = (s.strip() for s in unprefixed.strip().partition(" "))
        command = getattr(self, "command_" + command_name, self.unrecognized_command)
        try:
            logger.debug(f"Command {command_name} from {message.author}")
            await command(message, rest)
        except:
            logger.exception("Error while handling command")

    async def unrecognized_command(self, message, rest):
        pass


class ShuffleBot(BotBase):
    RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
    SUITS = "♣♦♥♠"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cards = [rank + suit for suit in self.SUITS for rank in self.RANKS]

    async def command_scandeck(self, message, rest):
        cards_str = ", ".join(self.cards)
        await message.channel.send(f"Cards in the deck: {spoiler(cards_str)}")


def spoiler(message):
    escaped = message.replace("|", r"\|")
    return "||" + escaped + "||"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    bot = ShuffleBot()
    bot.run(os.environ["DISCORD_TOKEN"])
