import re


def is_valid_email(v: str) -> bool:
    email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(email_pattern, v))
