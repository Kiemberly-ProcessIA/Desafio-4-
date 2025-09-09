FROM python:3.12-slim

WORKDIR /app

# Dependências básicas
RUN apt-get update && apt-get install -y curl make ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar o uv
RUN curl -LsSf https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz \
    -o uv.tar.gz \
    && tar -xzf uv.tar.gz \
    && mv uv*/uv /usr/local/bin/uv \
    && rm -rf uv* uv.tar.gz

# Copiar dependências primeiro (melhor cache)
COPY requirements.txt .

# Copiar código do projeto
COPY . .

CMD ["bash"]
