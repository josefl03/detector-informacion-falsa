# Build ollama and install models
FROM ollama/ollama:latest AS ollama
USER root

ENV OLLAMA_MODELS=/ollama/

COPY ./scripts/install-ollama.sh /tmp/install-ollama.sh
RUN chmod +x /tmp/install-ollama.sh && /tmp/install-ollama.sh

EXPOSE 11434