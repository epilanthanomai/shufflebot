import collections
import logging
import os
import random

import discobot

logger = logging.getLogger("shufflebot")

Card = collections.namedtuple("Card", ["name", "description"])


class CardStack:
    def __init__(self, cards):
        self.card_set = cards
        self.reset()

    def reset(self):
        self.cards = self.card_set.copy()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            return
        card, self.cards = self.cards[0], self.cards[1:]
        return card


POKER_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
POKER_SUITS = "♣♦♥♠"
POKER_CARDS = [
    Card(name=rank + suit, description=None)
    for suit in POKER_SUITS
    for rank in POKER_RANKS
]


class ShuffleBot(discobot.BotBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channels = {}

    def get_cards(self, channel, create=True):
        result = self.channels.get(channel.id)
        if result is None:
            result = CardStack(POKER_CARDS)
            self.channels[channel.id] = result
        return result

    async def command_scandeck(self, message, rest):
        """Output the entire contents of the deck. It'll be spoilered in a channel."""
        cards = self.get_cards(message.channel)
        cards_str = ", ".join(card.name for card in cards.cards)
        await message.channel.send(
            f"{len(cards.cards)} cards in the deck: "
            + discobot.maybe_spoiler(cards_str, message.channel)
        )

    async def command_reset(self, message, rest):
        """Reset the deck to its original, unshuffled state."""
        cards = self.get_cards(message.channel)
        cards.reset()
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
        elif discobot.single_peer(message.channel):
            await message.channel.send(format_card_message(card))
        else:
            await message.channel.send(
                f"{message.author.mention} drew "
                f"{discobot.spoiler(format_card_message(card))}"
            )


def format_card_message(card):
    if card.description is not None:
        return f'"{card.name}"\n' + discobot.quote_all(card.description)
    else:
        return card.name


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    version = discobot.__version__ or "dev"
    logger.info("shufflebot version=" + version)
    bot = ShuffleBot()
    bot.run(os.environ["DISCORD_TOKEN"])
