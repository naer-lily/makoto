FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e .

EXPOSE 8000

ENV MAKOTO_HOST=0.0.0.0
ENV MAKOTO_PORT=8000

CMD ["makoto-server"]
