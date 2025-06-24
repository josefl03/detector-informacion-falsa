FROM python:3.12-slim AS backend
USER root

WORKDIR /app

COPY ./backend ./backend/
COPY ./libreria ./libreria/
COPY .env .

COPY ./requirements.txt .

RUN pip install -r requirements.txt
RUN pip install google-genai==1.21.1

RUN apt update -y
RUN apt install -y ffmpeg
RUN yes | playwright install-deps
RUN yes | playwright install

RUN pip install -e libreria/fake_news_detector

EXPOSE 8000

CMD ["python3", "/app/backend/backend.py"]