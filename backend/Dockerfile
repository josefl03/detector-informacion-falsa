FROM python:3.12-slim AS backend
USER root

WORKDIR /backend

COPY ./backend ./backend/
COPY ./libreria ./libreria/
COPY .env .

COPY ./requirements.txt .

RUN pip install -r requirements.txt

RUN apt update -y
RUN apt install -y ffmpeg
RUN yes | playwright install-deps
RUN yes | playwright install

RUN pip install -e libreria/fake_news_detector

EXPOSE 8000

CMD ["python3", "/backend/backend.py"]