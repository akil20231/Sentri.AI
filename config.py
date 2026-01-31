import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _csv_ids(s: str) -> set[int]:
    if not s:
        return set()
    return {int(x.strip()) for x in s.split(",") if x.strip()}

@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int
    monitored_channels: set[int]
    mod_log_channel_id: int
    quarantine_role_name: str

    warn_threshold: float
    throttle_threshold: float
    quarantine_threshold: float
    throttle_seconds: int

def get_settings() -> Settings:
    return Settings(
        token=os.environ["DISCORD_BOT_TOKEN"],
        guild_id=int(os.environ["GUILD_ID"]),
        monitored_channels=_csv_ids(os.getenv("MONITORED_CHANNEL_IDS", "")),
        mod_log_channel_id=int(os.environ["MOD_LOG_CHANNEL_ID"]),
        quarantine_role_name=os.getenv("QUARANTINE_ROLE_NAME", "Quarantined"),

        warn_threshold=float(os.getenv("WARN_THRESHOLD", "0.35")),
        throttle_threshold=float(os.getenv("THROTTLE_THRESHOLD", "0.55")),
        quarantine_threshold=float(os.getenv("QUARANTINE_THRESHOLD", "0.75")),
        throttle_seconds=int(os.getenv("THROTTLE_SECONDS", "20")),
    )
