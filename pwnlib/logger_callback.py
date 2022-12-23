from typing import Callable
from pwnlib.level import Level

LoggerCallback = Callable[[Level, str], None]
