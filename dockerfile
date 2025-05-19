FROM python:3.12.4-slim

WORKDIR /app

# dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# mounting dirs
RUN mkdir -p logs

# port
EXPOSE 8000

# run command
CMD ["python", "run.py"]