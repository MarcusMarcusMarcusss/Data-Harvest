from dataclasses import dataclass
import time

@dataclass
class ExtractedURLEntry:
    itemid: int
    URLString: str
    Location: str
    TimeStamp: str

