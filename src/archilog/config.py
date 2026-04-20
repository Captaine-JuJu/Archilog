from dataclasses import dataclass

@dataclass
class Config:
    DATABASE_URL: str
    DEBUG: bool

config = Config(
    DATABASE_URL="sqlite:///database.db",
    DEBUG=True
)