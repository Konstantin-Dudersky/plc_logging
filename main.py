#!/usr/bin/env python3
"""Script for logging messages from plc."""

import asyncio
import logging
import os
import sys
from asyncio.streams import StreamReader, StreamWriter
from enum import IntEnum
from logging import Handler, handlers
from typing import List


FORMAT: str = "%(levelname)s | %(message)s"


# ------------------------------------------------------------------------------


class LoggerLevel(IntEnum):
    """Logging levels."""

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


# Formatters -------------------------------------------------------------------


class StreamFormatter(logging.Formatter):
    """Custom formatter for console output."""

    GREEN = "\x1b[32;20m"
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    def get_format(self: "StreamFormatter", text: str, levelno: int) -> str:
        """Цвет сообщения.

        :param text: текст, цвет которого нужно изменить
        :param levelno: класс сообщения
        :return: текст с измененным текстом
        """
        match levelno:
            case logging.DEBUG:
                return self.GREY + text + self.RESET
            case logging.INFO:
                return self.GREEN + text + self.RESET
            case logging.WARNING:
                return self.YELLOW + text + self.RESET
            case logging.ERROR:
                return self.RED + text + self.RESET
            case logging.CRITICAL:
                return self.BOLD_RED + text + self.RESET
        return text

    def format(self: "StreamFormatter", record: logging.LogRecord) -> str:
        """Format function.

        :param record: запись логгера
        :return: отформатированная запись логгера
        """
        log_fmt = self.get_format(FORMAT, record.levelno)
        formatter = logging.Formatter(log_fmt)
        return (
            formatter.format(record)
            + "\n"
            + self.get_format("-" * 80, record.levelno)
        )


class FileFormatter(logging.Formatter):
    """Custom formatter for file output."""

    def format(self: "FileFormatter", record: logging.LogRecord) -> str:
        """Format function.

        :param record: запись логгера
        :return: отформатированная запись логгера
        """
        formatter = logging.Formatter(FORMAT)
        return formatter.format(record) + "\n" + "-" * 80


# Loggers ----------------------------------------------------------------------

os.makedirs("logs", exist_ok=True)

_handlers: List[Handler] = []
# логгирование в файл
file_handler = handlers.RotatingFileHandler(
    filename="logs/log.log",
    mode="a",
    maxBytes=5 * 1024 * 1024,
    backupCount=2,
    encoding=None,
    delay=False,
)
file_handler.setFormatter(FileFormatter())
_handlers.append(file_handler)
# логгирование в консоль
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(StreamFormatter())
_handlers.append(stream_handler)

logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    handlers=_handlers,
)


# ------------------------------------------------------------------------------


log = logging.getLogger(__name__)
log.setLevel(LoggerLevel.DEBUG)


class Handle:
    """Handle messages from client."""

    __init: bool = True

    async def handle(
        self: "Handle",
        reader: StreamReader,
        writer: StreamWriter,
    ) -> None:
        """Handle messages from client.

        :param reader: asyncio reader
        :param writer: asyncio writer
        """
        if self.__init:
            self.__init = False
            log.info(
                "conected device: %s",
                writer.get_extra_info("peername"),
            )
        data: bytes = await reader.read(254)
        length: int = data[1]
        message: str = data[2 : length + 2].decode(  # noqa: E203
            encoding="utf-8",
        )
        message_parts: List[str] = message.split("\t")
        len_at_least: int = 4
        if len(message_parts) < len_at_least:
            log.error(
                (
                    "not enough message parts, found: %s,"
                    " expected at least: %s,\nmessage: %s"
                ),
                len(message_parts),
                len_at_least,
                message,
            )
            return
        msg_level: str = message_parts[0]
        msg_ts: str = message_parts[1]
        msg_block_title: str = message_parts[2]
        msg_text: str = message_parts[3]
        if len(message_parts) > len_at_least:
            msg_values: List[str] = message_parts[len_at_least:]
        else:
            msg_values: List[str] = []
        match msg_level:
            case "+0":
                log_level = log.debug
            case "+1":
                log_level = log.info
            case "+2":
                log_level = log.warning
            case "+3":
                log_level = log.error
            case "+4":
                log_level = log.critical
            case _:
                log.error("incorrect logging level, actual: %s", msg_level)
                return
        try:
            log_level(
                "%s | %s\n%s",
                msg_ts,
                msg_block_title,
                msg_text.format(*msg_values),
            )
        except ValueError as exc:
            log.error(
                "incorrect message format\nmessage: %s\nerror: %s",
                message,
                exc,
            )
            return
        except IndexError as exc:
            log.error(
                "incorrect message format\nmessage: %s\nerror: %s",
                message,
                exc,
            )
            return


async def main() -> None:
    """Entry point."""
    argv: List[str] = sys.argv
    if len(argv) >= 2:
        port: int = int(sys.argv[1])
    else:
        port: int = 4567

    server = await asyncio.start_server(Handle().handle, port=port)

    log.info("Serving on %s", [s.getsockname() for s in server.sockets])

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
