import random
from datetime import datetime


def generate_order_no() -> str:
    """生成唯一的订单号 (时间戳 + 随机数)"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_digits = "".join([str(random.randint(0, 9)) for _ in range(6)])
    return f"{timestamp}{random_digits}"
