FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

EXPOSE 8000

COPY src/ .

CMD uvicorn main:app --host 0.0.0.0 --port 8000