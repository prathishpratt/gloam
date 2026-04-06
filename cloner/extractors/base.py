from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class ExtractedContent:
    title: str
    author: Optional[str]
    publish_date: Optional[date]
    main_html: str
    cover_image_url: Optional[str]
    description: Optional[str]


class BaseExtractor(ABC):
    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    def extract(self) -> ExtractedContent:
        pass
