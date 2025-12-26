from builtins import Exception


# 重复资源错误
class DuplicateResourceError(Exception):
    pass


# 校验异常
class ValidationError(Exception):
    pass
