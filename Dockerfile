FROM python:3-slim

LABEL org.opencontainers.image.source=https://github.com/mlesniew/birthdayreminder

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY birthday.py .

ENTRYPOINT ["python", "/app/birthday.py"]
