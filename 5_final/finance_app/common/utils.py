from datetime import datetime
from zoneinfo import ZoneInfo

def current_seoul_time():
    return datetime.now(tz=ZoneInfo("Asia/Seoul"))
