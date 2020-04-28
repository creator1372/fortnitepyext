from client import Client
import typing
import logging
import asyncio
import functools
from .command import Command
from .context import MessageContext
from .exceptions import NoPermissionError
if typing.TYPE_CHECKING:
    from fortnitepy.auth import Auth
    from typing import Any, Callable, Dict, Mapping, MutableMapping, List
    from ..party import PartyInvitation
    from ..message import FriendMessage

log = logging.getLogger(__name__)

class MainClient:
    # TODO
    # Make this implemented for fortnitepy and not for my bot
    def __init__(self, command_prefix, **kwargs):
        self.commands: Dict[str, Callable] = {}
        self._command_prefix = command_prefix
        self.client = None
        self._checks: List[Callable] = []

    @property
    def command_prefix(self):
        return self._command_prefix

    def register_command(self, command_name: str, function: Command) -> None:
        log.debug(f"registered {self.command_prefix}{command_name} as a"
                  "command")
        if not isinstance(function, Command):
            raise TypeError("Function must be a coroutine.")
        self.commands[f"{self.command_prefix}{command_name}"] = function

    async def get_permission(self, message: 'MessageContext') -> bool:
        for pred in self._checks:
            if not await pred():
                return False
        return True

    async def process_command(self, command, message) -> None:
        log.debug(f"Processing {command.__name__} as a command")
        permission = self.get_permission(message)
        if not permission:
            log.debug(
                f"{message.author.display_name} doesn't have permission"
                " to run this command, skipping")
            return
        return await command(MessageContext(message))

    async def test_commands(self, message: 'FriendMessage') -> None:
        log.debug(f"Received message: {message.content}")
        command, *_ = message.content.split(" ")
        if not command.startswith(self.command_prefix):
            return
        if command in self.commands.keys():
            await self.process_command(self.commands[command], message)

    def command(self,
                coro: Callable
                ) -> Callable[['FriendMessage'], Any]:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("Function must be a coroutine")
        self.register_command(coro.__name__, Command(coro, self.command_prefix)
                              )

        def inner(*args, **kwargs):
            return coro(*args, **kwargs)
        return inner

    @staticmethod
    def get_code():
        return input("Exchange code? ")

    async def on_ready(self):
        colored_print(f"ready as {self.client.user.display_name}", Color.GREEN)

    def start(self):
        self.client = fortnitepy.Client(
            auth=fortnitepy.AdvancedAuth(
                email=self.email,
                exchange_code=self.get_code,
                device_id=self.device_id,
                account_id=self.client_id,
                secret=self.secret
            )
        )
        self.client.add_event_handler("friend_message", self.test_commands)
        self.client.add_event_handler("party_message", self.test_commands)
        self.client.add_event_handler("ready", self.on_ready)
        self.client.add_event_handler("party_invite", self.on_invite)

    def on_invite(self, invite: 'PartyInvitation'):
        pass

    def bind_to_http_client(self):
        self.http = HttpClient(self.client)

    @functools.wraps
    def owner_only(self, function: Command):
        def inner(message: 'MessageContext', *args, **kwargs):
            if not self.get_permission(message):
                raise NoPermissionError("No permission to run command")
            else:
                return function(*args, **kwargs)
        return inner
