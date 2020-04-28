import fortnitepy
from typing import Union
from enum import Enum


class MessageType(Enum):
    PARTY = 0
    FRIEND = 1


class MessageContext(fortnitepy.message.MessageBase):
    def __init__(self,
                 message: Union[fortnitepy.FriendMessage, fortnitepy.PartyMessage]  # noqa
                 ) -> None:
        self._client = message.client
        self._author = message.author # type: ignore
        self._content = message.content
        self._created_at = message._created_at
        self._message = message
        if isinstance(message, fortnitepy.PartyMessage):
            self.party = self._message.party # type: ignore # noqa
        else:
            self.party = None
        if isinstance(message, fortnitepy.FriendMessage):
            self.type = MessageType.FRIEND
        else:
            self.type = MessageType.PARTY

    async def reply(self, content: str) -> None:
        """|coro|

        Replies to the message with the given content.

        Parameters
        ----------
        content: :class:`str`
            The content of the message
        """
        if self.type == MessageType.FRIEND:
            return await self.author.send(content)
        return await self.party.send(content)
