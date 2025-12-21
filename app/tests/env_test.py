import os
import sys

from dotenv import load_dotenv

# 输出python解释器所处位置
print(sys.prefix)

load_dotenv()
postgres_user = os.getenv("POSTGRES_USER")
# 输出POSTGRES_USER环境变量的值
print(postgres_user)
