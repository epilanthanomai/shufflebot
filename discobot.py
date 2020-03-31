import inspect
import logging
import os

from discord import Client

logger = logging.getLogger("shufflebot." + __name__)
__version__ = os.environ.get("SHUFFLEBOT_VERSION")


class BotBase(Client):
    BOT_NAME = "Discobot"
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
            await message.add_reaction("💥")

    async def command_help(self, message, rest):
        await message.channel.send(self.get_formatted_help())

    def get_formatted_help(self):
        version_str = f"v{__version__}" if __version__ else "dev"
        version_statement = bold(self.BOT_NAME) + " " + version_str

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

        return version_statement + "\n" + "\n".join(formatted)

    def command_from_attribute_name(self, attr_name):
        assert attr_name.startswith("command_")
        command_name = attr_name[len("command_") :]
        return self.command_prefix + command_name

    def format_command_help(self, name, doc):
        return quote(fixed_width(name) + " " + doc)

    async def unrecognized_command(self, message, rest):
        pass


def single_peer(channel):
    # If a channel has only a single recipient, then it is a private DM channel, and we might
    # wnat to escape our message differently.
    return hasattr(channel, "recipient")


async def fail_command(message, result):
    if not single_peer(message.channel):
        result = message.author.mention + ": " + result
    await message.channel.send(result)
    await message.add_reaction("🙁")


def bold(text):
    escaped = text.replace("**", r"\*\*")
    return "**" + escaped + "**"


def spoiler(text):
    escaped = text.replace("|", r"\|")
    return "||" + escaped + "||"


def maybe_spoiler(text, channel):
    if single_peer(channel):
        return text
    else:
        return spoiler(text)


def quote(line):
    return "> " + line


def quote_all(text):
    return ">>> " + text


def fixed_width(text):
    tick = "`"
    if "`" in text:
        tick = "``"
    # I haven't found a way to safely wrap a double backtick in discord yet, so I guess just
    # look ugly when that happens?

    return f"{tick}{text}{tick}"
