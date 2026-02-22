REGISTER_SUCCESS = "注册成功"
USERNAME_OR_EMAIL_EXISTS = "用户名或邮箱已存在"
INVALID_CAPTCHA = "验证码错误或已过期"
PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT = "密码需同时包含字母和数字"
USERNAME_CANNOT_BE_EMAIL = "用户名不能为邮箱格式"
DUPLICATE_RESOURCE_ERROR = "资源重复"
UNKNOWN_ERROR = "未知错误"
VALIDATION_ERROR = "校验错误"
LOGIN_SUCCESS = "登录成功"
INVALID_CREDENTIALS = "账号或密码错误"
CHANGE_PASSWORD_SUCCESS = "密码修改成功"
OLD_PASSWORD_ERROR = "旧密码错误"
USER_NOT_FOUND = "用户不存在"
NEW_PASSWORD_SAME_AS_OLD = "新密码不能与旧密码相同"
CAPTCHA_GENERATE_SUCCESS = "验证码生成成功"
REFRESH_TOKEN_INVALID = "刷新令牌无效或已过期"
TOO_MANY_REQUESTS = "请求过于频繁，请稍后再试"
REFRESH_TOKEN_SUCCESS = "刷新令牌成功"
ACCESS_TOKEN_EXPIRED = "访问令牌已过期"
ACCESS_TOKEN_INVALID = "访问令牌无效"
PERMISSION_DENIED = "权限不足"
# WWW-Authenticate headers
WWW_AUTH_EXPIRED = (
    'Bearer error="invalid_token", error_description="The access token expired"'
)
WWW_AUTH_INVALID = 'Bearer error="invalid_token", error_description="The access token is invalid or malformed"'

# 商家相关
MERCHANT_NOT_FOUND = "商家信息不存在"
PRODUCT_NOT_FOUND = "商品不存在"
PRODUCT_SKU_EXISTS = "商品SKU已存在"
PRODUCT_CREATE_SUCCESS = "商品创建成功"
PRODUCT_UPDATE_SUCCESS = "商品更新成功"
PRODUCT_STATUS_UPDATE_SUCCESS = "商品状态更新成功"
MERCHANT_UPDATE_SUCCESS = "商家信息更新成功"
GET_SUCCESS = "获取成功"
POST_SUCCESS = "操作成功"
PRODUCT_DELETE_SUCCESS = "商品删除成功"

# 购物车相关
CART_ADD_SUCCESS = "添加购物车成功"
CART_UPDATE_SUCCESS = "更新购物车成功"
CART_REMOVE_SUCCESS = "移除购物车商品成功"
CART_CLEAR_SUCCESS = "清空购物车成功"
PRODUCT_STOCK_NOT_ENOUGH = "商品库存不足"
PRODUCT_OFF_SHELF = "商品已下架"
ORDER_CANCEL_SUCCESS = "订单取消成功"
ORDER_STATUS_ERROR = "订单状态不可取消"
ORDER_PAY_SUCCESS = "订单支付成功"
ORDER_SHIP_SUCCESS = "订单发货成功"
ORDER_RECEIPT_SUCCESS = "确认收货成功"

# 收藏相关
FAVORITE_ADD_SUCCESS = "收藏成功"
FAVORITE_REMOVE_SUCCESS = "取消收藏成功"

# 社区相关
# 社区相关
COMMUNITY_GROUP_EXISTS = "话题圈名称已存在"
COMMUNITY_GROUP_NOT_FOUND = "话题圈不存在"
