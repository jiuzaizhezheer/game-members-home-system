# 多阶段构建：构建阶段
FROM python:3.12 as builder

WORKDIR /app

# 复制依赖文件
COPY pyproject.toml pdm.lock ./

# 安装 PDM 并安装依赖
RUN pip install pdm
RUN pdm export --without-hashes -o requirements.txt
RUN pip install --user -r requirements.txt

# 多阶段构建：运行阶段
FROM python:3.12-slim

WORKDIR /app

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 从构建阶段复制已安装的依赖
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/pyproject.toml /app/pdm.lock ./

# 复制应用代码
COPY . .

# 更改所有权
RUN chown -R appuser:appuser /app
USER appuser

# 将用户本地bin目录添加到PATH
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
