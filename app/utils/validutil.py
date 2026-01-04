import re


def is_valid_email(v: str) -> bool:
    """验证字符串是否为邮箱格式"""
    email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(email_pattern, v))


def id_password_has_letter_and_digit(v: str) -> bool:
    """验证密码是否包含字母和数字"""
    return bool(re.search(r"(?=.*[A-Za-z])(?=.*\d)", v))
