import logging
import os
import random

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


class CardStack:
    RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
    SUITS = "♣♦♥♠"

    def __init__(self):
        self.reset()

    def reset(self):
        self.cards = [rank + suit for suit in self.SUITS for rank in self.RANKS]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            return
        card, self.cards = self.cards[0], self.cards[1:]
        return card


class ShuffleBot(BotBase):
    NO_CARDS_MESSAGE = "This channel has no cards right now. +reset to start."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channels = {}

    def get_cards(self, channel, create=True):
        result = self.channels.get(channel.id)
        if result is None:
            result = CardStack()
            self.channels[channel.id] = result
        return result

    async def command_scandeck(self, message, rest):
        cards = self.get_cards(message.channel)
        cards_str = ", ".join(cards.cards)
        await message.channel.send(
            f"{len(cards.cards)} cards in the deck: {spoiler(cards_str)}"
        )

    async def command_reset(self, message, rest):
        self.channels[message.channel.id] = CardStack()
        await message.add_reaction("👍")

    async def command_shuffle(self, message, rest):
        cards = self.get_cards(message.channel)
        cards.shuffle()
        await message.add_reaction("🎲")

    async def command_draw(self, message, rest):
        cards = self.get_cards(message.channel)
        card = cards.draw()
        if card:
            await message.channel.send(f"{message.author.mention} drew {spoiler(card)}")
        else:
            await message.channel.send("There are no cards left in the deck.")


def spoiler(message):
    escaped = message.replace("|", r"\|")
    return "||" + escaped + "||"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    bot = ShuffleBot()
    bot.run(os.environ["DISCORD_TOKEN"])
