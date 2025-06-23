FROM python:3.12-slim

USER root

WORKDIR /usr/src/app

# Install the backend
COPY backend ./
COPY libreria ./
COPY requirements.txt ./

COPY webapp ./

COPY scripts/install-python-deps.sh ./
COPY scripts/install-node-deps.sh ./

RUN chmod +x install-node-deps.sh && ./install-node-deps.sh
RUN chmod +x install-python-deps.sh && ./install-python-deps.sh

# backend
EXPOSE 8000
# webapp
EXPOSE 1234

CMD ["python3", "backend/backend.py"]