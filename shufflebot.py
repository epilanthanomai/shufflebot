import inspect
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

    async def command_help(self, message, rest):
        await message.channel.send(self.get_formatted_help())

    def get_formatted_help(self):
        candidates = [
            (name, getattr(self, name))
            for name in dir(self)
            if name.startswith("command_")
        ]
        commands = [
            (self.command_from_attribute_name(name), command.__doc__)
            for (name, command) in candidates
            if inspect.iscoroutinefunction(command) and command.__doc__
        ]
        formatted = [self.format_command_help(name, doc) for (name, doc) in commands]
        return quote_all("\n".join(formatted))

    def command_from_attribute_name(self, attr_name):
        assert attr_name.startswith("command_")
        command_name = attr_name[len("command_") :]
        return self.command_prefix + command_name

    def format_command_help(self, name, doc):
        return fixed_width(name) + " " + doc

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
        """Output the entire contents of the deck. It'll be spoilered in a channel."""
        cards = self.get_cards(message.channel)
        cards_str = ", ".join(cards.cards)
        await message.channel.send(
            f"{len(cards.cards)} cards in the deck: "
            + maybe_spoiler(cards_str, message.channel)
        )

    async def command_reset(self, message, rest):
        """Reset the deck to its original, unshuffled state."""
        self.channels[message.channel.id] = CardStack()
        await message.add_reaction("👍")

    async def command_shuffle(self, message, rest):
        """Shuffle the cards in the deck."""
        cards = self.get_cards(message.channel)
        cards.shuffle()
        await message.add_reaction("🎲")

    async def command_draw(self, message, rest):
        """Draw one card from the deck, and send that card, spoilered, to the channel."""
        cards = self.get_cards(message.channel)
        card = cards.draw()
        if not card:
            await message.channel.send("There are no cards left in the deck.")
        elif single_peer(message.channel):
            await message.channel.send(card)
        else:
            await message.channel.send(f"{message.author.mention} drew {spoiler(card)}")


def single_peer(channel):
    # If a channel has only a single recipient, then it is a private DM channel, and we might
    # wnat to escape our message differently.
    return hasattr(channel, "recipient")


def spoiler(text):
    escaped = text.replace("|", r"\|")
    return "||" + escaped + "||"


def maybe_spoiler(text, channel):
    if single_peer(channel):
        return text
    else:
        return spoiler(text)


def quote_all(text):
    return ">>> " + text


def fixed_width(text):
    tick = "`"
    if "`" in text:
        tick = "``"
    # I haven't found a way to safely wrap a double backtick in discord yet, so I guess just
    # look ugly when that happens?

    return f"{tick}{text}{tick}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    bot = ShuffleBot()
    bot.run(os.environ["DISCORD_TOKEN"])
