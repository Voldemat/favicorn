from dataclasses import dataclass


@dataclass
class Config:
    keepalive_timeout_s: float = 5
    tasks_wait_timeout_s: float = 5
