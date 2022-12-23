from __future__ import annotations
from socket import socket
from types import TracebackType
from typing import Literal, TypeVar
from pwnlib.level import Level
from pwnlib.logger_callback import LoggerCallback

Self = TypeVar("Self", bound="Connection")


class Connection:
    host: str
    port: int
    socket: socket
    data: bytes
    log_callback: LoggerCallback | None

    TIMEOUT = 5.0
    MAX_RECEIVE_SIZE = 0x200

    def __init__(
        self,
        host: str,
        port: int,
        log_callback: LoggerCallback | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.data = b""
        self.log_callback = log_callback

        self.socket = socket()
        self.socket.settimeout(self.TIMEOUT)
        self.socket.connect((self.host, self.port))

        self.info(f"Connected to {(self.host, self.port)}")

    def log(self, level: Level, message: object) -> None:
        if self.log_callback is not None:
            self.log_callback(level, str(message))

    def trace(self, message: object) -> None:
        return self.log(Level.TRACE, message)

    def info(self, message: object) -> None:
        return self.log(Level.INFO, message)

    def debug(self, message: object) -> None:
        return self.log(Level.DEBUG, message)

    def error(self, message: object) -> None:
        return self.log(Level.ERROR, message)

    def success(self, message: object) -> None:
        return self.log(Level.SUCCESS, message)

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_instance: BaseException | None,
        exception_backtrace: TracebackType | None,
    ) -> bool:
        self.close()

        if exception_instance is None:
            self.success("Done")
            return True

        if isinstance(exception_instance, RuntimeError):
            self.error(str(exception_instance))
            return True

        return False

    def close(self) -> None:
        self.socket.close()
        self.info(f"Disconnected from {(self.host, self.port)}")

    def read_raw(self, byte_count: int) -> bytes:
        while len(self.data) < byte_count:
            self.data += self.socket.recv(byte_count - len(self.data))

        result, self.data = self.data[:byte_count], self.data[byte_count:]
        self.trace(f"-> {result!r}")
        return result

    def read_until(self, value: bytes, include: bool = True) -> bytes:
        while True:
            if (index := self.data.find(value)) != -1:
                if include:
                    index += len(value)

                result, self.data = self.data[:index], self.data[index:]
                self.trace(f"-> {result!r}")
                return result

            self.data += self.socket.recv(Connection.MAX_RECEIVE_SIZE)

    def read_line(self) -> bytes:
        return self.read_until(b"\n")

    def read_lines(self, count: int) -> list[bytes]:
        return [self.read_line() for _ in range(count)]

    def write(self, value: bytes) -> None:
        self.socket.send(value)
        self.trace(f"<- {value!r}")

    def write_int(
        self,
        value: int,
        byte_count: int,
        byte_order: Literal["little", "big"] = "little",
        signed: bool = False,
    ) -> None:
        self.write(value.to_bytes(byte_count, byte_order, signed=signed))
