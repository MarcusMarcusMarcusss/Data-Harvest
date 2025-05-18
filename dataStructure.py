from dataclasses import dataclass
import time

@dataclass
class CoordinatorInfoEntry:
    CoordName: str
    CoordEmail: str

@dataclass
class UnitInfoEntry:
    CoordinatorID: str
    UnitName: str
    SchoolName:str


@dataclass
class ExtractedURLEntry:
    itemid: int
    URLString: str
    Location: str
    TimeStamp: str

@dataclass# files & Main pages
class ContentItemEntry: 
    Unitid: int
    FileName: str
    URL: str
    FileType: str

#adding below classes For nav & location
@dataclass 
class ForumDiscussionEntry:
    discussionid: int
    ForumName: str
    DiscussionTitle: str
    URL: str
    TimeStamp: str

@dataclass
class FolderFileEntry:
    fileid: int
    FolderName: str
    FileName: str
    URL: str
    TimeStamp: str

@dataclass
class PageLinkEntry:
    pageid: int
    PageTitle: str
    Link: str
    TimeStamp: str

@dataclass
class CoordinatorEntry:
    Name: str
    Email: str
    Department: str