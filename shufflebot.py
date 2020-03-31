import collections
import logging
import os
import random

import yaml

import discobot

logger = logging.getLogger("shufflebot")

Card = collections.namedtuple("Card", ["name", "description"])
CardSet = collections.namedtuple("CardSet", ["name", "description", "cards"])


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


class ShuffleBot(discobot.BotBase):
    BOT_NAME = "Shufflebot"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channels = {}
        self.library = self.load_decks("decks/poker.yaml")
        self.default_card_set = list(sorted(self.library.keys()))[0]

    def load_decks(self, path):
        with open(path) as decks_f:
            card_set_list = [
                card_set_from_yaml_object(yaml_object)
                for yaml_object in yaml.load_all(decks_f, Loader=yaml.Loader)
            ]
        return {cs.name: cs for cs in card_set_list}

    def get_formatted_help(self):
        super_result = super().get_formatted_help()
        local_help = (
            f"{discobot.bold(self.BOT_NAME)} knows about the following decks: "
            + " ".join(discobot.fixed_width(name) for name in self.library.keys())
        )
        return super_result + "\n" + local_help

    def get_cards(self, channel, create=True):
        result = self.channels.get(channel.id)
        if result is None:
            result = CardStack(self.library[self.default_card_set])
            self.channels[channel.id] = result
        return result

    async def command_newdeck(self, message, rest):
        """Use a new deck of the specified type in this channel."""
        if not rest:
            return await discobot.fail_command(
                message, "You must specify a deck type to use."
            )
        card_set = self.library.get(rest)
        if not card_set:
            return await discobot.fail_command(
                message, f"No deck named {discobot.fixed_width(rest)}"
            )
        self.channels[message.channel.id] = CardStack(card_set.cards)
        await message.add_reaction("👍")

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
            return await discobot.fail_command(
                message, "There are no cards left in the deck."
            )
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


def card_set_from_yaml_object(yaml_deck):
    name = yaml_deck["name"]
    description = yaml_deck.get("description")
    cards = [card_from_yaml_object(yaml_card) for yaml_card in yaml_deck["cards"]]
    assert cards
    return CardSet(name=name, description=description, cards=cards)


def card_from_yaml_object(yaml_card):
    name = yaml_card["name"]
    description = yaml_card.get("description")
    return Card(name=name, description=description)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    version = discobot.__version__ or "dev"
    logger.info("shufflebot version=" + version)
    bot = ShuffleBot()
    bot.run(os.environ["DISCORD_TOKEN"])
