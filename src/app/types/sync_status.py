from enum import StrEnum


class SyncStatus(StrEnum):
    NEVER = 'never'
    RUNNING = 'running'
    SUCCESS = 'success'
