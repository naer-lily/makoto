# Stage 1: build frontend
FROM node:22-alpine AS web-builder

WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: run server
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
COPY --from=web-builder /web/dist web/dist/

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e .

EXPOSE 8000

ENV MAKOTO_HOST=0.0.0.0
ENV MAKOTO_PORT=8000

CMD ["makoto-server"]
