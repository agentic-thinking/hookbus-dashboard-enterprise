FROM python:3.12-slim
LABEL org.opencontainers.image.title="HookBus Dashboard Enterprise"
LABEL org.opencontainers.image.version="1.0.0a1"
LABEL org.opencontainers.image.vendor="Agentic Thinking Limited"
LABEL org.opencontainers.image.description="Enterprise operator dashboard for HookBus + AgentSpend"
WORKDIR /app
COPY hookbus_dashboard_enterprise/ /app/hookbus_dashboard_enterprise/
COPY pyproject.toml /app/
EXPOSE 8901
ENV HOOKBUS_DASHBOARD_PORT=8901
ENTRYPOINT ["python3", "-m", "hookbus_dashboard_enterprise"]
