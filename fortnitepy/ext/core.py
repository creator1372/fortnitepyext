from typing import Callable, Dict, Any
from inspect import signature
from enum import Enum
import asyncio
import functools
import logging
from .exceptions import InvalidParameters, NoPermissionError
from .context import MessageContext

log = logging.getLogger(__name__)


class Mode(Enum):
    POSITIONAL = 0
    NON_POSITIONAL = 1
    OWNER_ONLY = 2
    FREE = 3


class Parameter(Enum):
    CONTEXT = 0
    POSITIONAL = 1
    NON_POSITIONAL = 2


class Command:
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.__original_kwargs__ = kwargs.copy()
        return self

    def __init__(self, fn: Callable, **kwargs):
        self.signature = signature(fn)
        self.function = fn
        self.uses_non_positional = False
        self.parse_params()
        try:
            self.prefix = kwargs.pop("prefix")
        except KeyError:
            self.prefix = kwargs.pop("parent").command_prefix
        self.mode = Mode.FREE
        self.checks = [] # type: ignore
        functools.update_wrapper(self, fn)

    def parse_params(self):
        args = str(self.signature)[1:-1:].replace(" ", "").split(",")
        mode = Mode.POSITIONAL
        self.length = len(args)
        if args == ['']:
            raise InvalidParameters()
        args[0] = Parameter.CONTEXT
        for index, arg in enumerate(args[1:], 1):
            if arg == "*":
                mode = Mode.NON_POSITIONAL
                self.length -= 1
                continue
            if mode == Mode.POSITIONAL:
                args[index] = Parameter.POSITIONAL
            if mode == Mode.NON_POSITIONAL:
                args[index] = Parameter.NON_POSITIONAL
            if mode == Mode.NON_POSITIONAL:
                break
        self.params = args

    def add_check(self, pred):
        log
        if not asyncio.iscoroutinefunction(pred):
            pred = asyncio.coroutine(pred)
        self.checks.append(pred)

    async def __call__(self, message: MessageContext, user: str = None):
        checks = []
        for check in self.checks:
            checks.append(check())
        result = any(await asyncio.gather(*checks))
        if not result:
            raise NoPermissionError("Predicate returned False")
        message._content = message.content[len(
            self.prefix + self.function.__name__ + " "):
            ]  # Removes the invoker
        if self.mode == Mode.FREE:
            return await self.function(message)
        elif self.mode == Mode.OWNER_ONLY and not user:
            return await self.function(message)
        elif self.mode == Mode.OWNER_ONLY and user:
            return await self.function(message)
        else:
            raise NoPermissionError

# In progress # noqa