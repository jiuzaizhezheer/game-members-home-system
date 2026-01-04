import hashlib
import os
import secrets


def _pbkdf2_hash(password: str, salt: bytes, iterations: int = 480000) -> bytes:
    """使用 PBKDF2-HMAC-SHA256 算法对密码进行哈希"""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    iterations = 480000
    salt = os.urandom(16)
    digest = _pbkdf2_hash(password, salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """验证密码是否与哈希值匹配"""
    try:
        algo, iter_str, salt_hex, digest_hex = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        computed = _pbkdf2_hash(password, salt, iterations)
        return secrets.compare_digest(computed, expected)
    except Exception:
        return False
