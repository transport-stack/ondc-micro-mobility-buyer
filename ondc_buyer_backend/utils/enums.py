from enum import Enum
from datetime import timedelta


class ActionTTL(Enum):
    SEARCH = 30
    SELECT = 180
    INIT = 30
    CONFIRM = 180
    TRACK = 30
    CANCEL = 30
    STATUS = 30


def get_ttl_delta(action_name):
    # Use getattr to dynamically access enum values
    action_value = getattr(ActionTTL, action_name, None)
    if action_value is None:
        raise ValueError(f"No such action '{action_name}' in ActionTTL enum")
    return timedelta(seconds=action_value.value)
