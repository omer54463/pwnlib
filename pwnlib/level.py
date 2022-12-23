from enum import Enum, auto


class Level(Enum):
    TRACE = auto()
    INFO = auto()
    DEBUG = auto()
    WARNING = auto()
    ERROR = auto()
    SUCCESS = auto()
