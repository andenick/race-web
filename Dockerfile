# DuBois — race.heterodata.org. FastAPI + Jinja2 + Plotly, stock-only stack.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

EXPOSE 8090
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", "-w", "2", \
     "-b", "0.0.0.0:8090", "--timeout", "120"]
