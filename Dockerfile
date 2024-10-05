FROM python:3.12

# Timezone
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ='Europe/Oslo'
RUN apt-get update && apt-get install -y tzdata && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install dependencies and copy source code
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the disc folder to the container
COPY disc/ .

CMD ["python", "main.py"]
