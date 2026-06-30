from dataclasses import dataclass, field


@dataclass
class AppState:
    enabled: bool = False
    positions: dict = field(default_factory=dict)  # {"KRW-BTC": "long"}


state = AppState()
