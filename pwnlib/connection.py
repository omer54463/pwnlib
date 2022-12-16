from __future__ import annotations
from select import select
from socket import socket
from sys import stdout
from types import TracebackType
from typing import Literal, Optional, Type
from loguru import Logger


class Connection:
    host: str
    port: int
    socket: socket
    data: bytes
    verbose: bool
    logger: Logger

    TIMEOUT = 5.0
    MAX_RECEIVE_SIZE = 0x200
    LOGGER_FORMAT = "[ {time:YYYY-MM-DD HH:mm:ss.SSS} ] | <level>{message}</level>"

    def __init__(self, host: str, port: int, verbose: bool = False) -> None:
        self.host = host
        self.port = port
        self.data = b""

        self.logger = Logger()
        self.logger.add(sink=stdout, format=self.LOGGER_FORMAT, level="TRACE")
        self.logger.configure(
            levels=[
                dict(name="TRACE", color="<white>"),
                dict(name="INFO", color="<white><bold>"),
                dict(name="ERROR", color="<red><bold>"),
                dict(name="SUCCESS", color="<green><bold>"),
            ]
        )

        self.socket = socket()
        self.socket.setblocking(False)
        self.socket.connect((self.host, self.port))

        self.verbose = verbose
        if self.verbose:
            self.logger.info(f"Connected to {(self.host, self.port)}")

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

    def recv(self, byte_count: int, timeout: float = TIMEOUT) -> bytes:
        read_ready, _, _ = select([self.socket], [], [], timeout)
        if len(read_ready) == 1:
            return self.socket.recv(byte_count)

        raise TimeoutError("Socket recv timed out")

    def close(self) -> None:
        self.socket.close()
        self.logger.info(f"Disconnected from {(self.host, self.port)}")

    def read_raw(self, byte_count: int) -> bytes:
        while len(self.data) < byte_count:
            self.data += self.recv(byte_count - len(self.data))

        result, self.data = self.data[:byte_count], self.data[byte_count:]
        if self.verbose:
            self.logger.info("->", result)
        return result

    def read_until(self, value: bytes, include: bool = True) -> bytes:
        while True:
            if (index := self.data.find(value)) != -1:
                if include:
                    index += len(value)

                result, self.data = self.data[:index], self.data[index:]
                if self.verbose:
                    self.logger.info("->", result)
                return result

            self.data += self.recv(Connection.MAX_RECEIVE_SIZE)

    def read_line(self) -> bytes:
        return self.read_until(b"\n")

    def read_lines(self, count: int) -> list[bytes]:
        return [self.read_line() for _ in range(count)]

    def send(self, value: bytes, timeout: float = TIMEOUT) -> None:
        _, write_ready, _ = select([], [self.socket], [], timeout)
        if len(write_ready) == 1:
            self.socket.send(value)

        raise TimeoutError("Socket send timed out")

    def write(self, value: bytes) -> None:
        self.send(value)
        if self.verbose:
            self.logger.info("<-", value)

    def write_int(
        self,
        value: int,
        byte_count: int,
        byte_order: Literal["little", "big"] = "little",
        signed: bool = False,
    ) -> None:
        self.write(value.to_bytes(byte_count, byte_order, signed=signed))

    def set_verbose(self, verbose: bool) -> None:
        self.verbose = verbose
