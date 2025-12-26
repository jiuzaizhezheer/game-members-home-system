from datetime import datetime


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")
