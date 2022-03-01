FROM python:3-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY birthday.py .

ENTRYPOINT ["python", "/app/birthday.py"]
