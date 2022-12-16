from __future__ import annotations
from socket import socket
from sys import stdout
from types import TracebackType
from typing import TYPE_CHECKING, Any, Iterable, Literal, Optional, Type
from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger


class Connection:
    host: str
    port: int
    socket: socket
    data: bytes
    logger: Logger

    TIMEOUT = 5.0
    MAX_RECEIVE_SIZE = 0x200
    LOGGER_FORMAT = "[ {time:YYYY-MM-DD HH:mm:ss.SSS} ] | <level>{message}</level>"

    def __init__(self, host: str, port: int, verbose: bool = False) -> None:
        self.host = host
        self.port = port
        self.data = b""

        self.logger = logger.bind(pwnlib=True)
        self.logger.remove()
        self.logger.add(
            sink=stdout,
            filter=lambda record: "pwnlib" in record["extra"],
            format=self.LOGGER_FORMAT,
            level="TRACE" if verbose else "INFO",
        )
        self.logger.configure(
            levels=[
                dict(name="TRACE", color="<white>"),
                dict(name="INFO", color="<white><bold>"),
                dict(name="DEBUG", color="<cyan><bold>"),
                dict(name="ERROR", color="<red><bold>"),
                dict(name="SUCCESS", color="<green><bold>"),
            ]
        )

        self.socket = socket()
        self.socket.settimeout(self.TIMEOUT)
        self.socket.connect((self.host, self.port))

        self.info(f"Connected to {(self.host, self.port)}")

    def trace(
        self,
        message: str,
        *args: Iterable[Any],
        **kwargs: dict[Any, Any],
    ) -> None:
        return self.logger.trace(message, *args, **kwargs)

    def info(
        self,
        message: str,
        *args: Iterable[Any],
        **kwargs: dict[Any, Any],
    ) -> None:
        return self.logger.info(message, *args, **kwargs)

    def debug(
        self,
        message: str,
        *args: Iterable[Any],
        **kwargs: dict[Any, Any],
    ) -> None:
        return self.logger.debug(message, *args, **kwargs)

    def error(
        self,
        message: str,
        *args: Iterable[Any],
        **kwargs: dict[Any, Any],
    ) -> None:
        return self.logger.error(message, *args, **kwargs)

    def success(
        self,
        message: str,
        *args: Iterable[Any],
        **kwargs: dict[Any, Any],
    ) -> None:
        return self.logger.success(message, *args, **kwargs)

    def __enter__(self) -> Connection:
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_instance: Optional[BaseException],
        exception_backtrace: Optional[TracebackType],
    ) -> Literal[False]:
        self.close()
        return False

    def close(self) -> None:
        self.socket.close()
        self.info(f"Disconnected from {(self.host, self.port)}")

    def read_raw(self, byte_count: int) -> bytes:
        while len(self.data) < byte_count:
            self.data += self.socket.recv(byte_count - len(self.data))

        result, self.data = self.data[:byte_count], self.data[byte_count:]
        self.trace("->", result)
        return result

    def read_until(self, value: bytes, include: bool = True) -> bytes:
        while True:
            if (index := self.data.find(value)) != -1:
                if include:
                    index += len(value)

                result, self.data = self.data[:index], self.data[index:]
                self.trace("->", result)
                return result

            self.data += self.socket.recv(Connection.MAX_RECEIVE_SIZE)

    def read_line(self) -> bytes:
        return self.read_until(b"\n")

    def read_lines(self, count: int) -> list[bytes]:
        return [self.read_line() for _ in range(count)]

    def write(self, value: bytes) -> None:
        self.socket.send(value)
        self.trace("<-", value)

    def write_int(
        self,
        value: int,
        byte_count: int,
        byte_order: Literal["little", "big"] = "little",
        signed: bool = False,
    ) -> None:
        self.write(value.to_bytes(byte_count, byte_order, signed=signed))
