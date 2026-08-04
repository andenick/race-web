# DuBois — race.heterodata.org. FastAPI + Jinja2 + Plotly, stock-only stack.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Deps: install everything except carson-telemetry from PyPI (it is VENDORED at
# ./vendor/carson-telemetry and is NOT on PyPI), then pip-install the local copy
# with its FastAPI extra. Two steps, not one, because pip cannot resolve the
# name from an index.
#
# WHY THE `COPY vendor` IS NOT OPTIONAL: if the vendor tree is missing, this RUN
# fails the BUILD loudly. The alternative — strip the requirement and hope the
# app's import is guarded — has shipped sites with a telemetry volume that was
# never written to for a month after launch. A missing vendor tree must break
# the build, never the measurement.
COPY app/requirements.txt /app/requirements.txt
COPY vendor /app/vendor
RUN grep -v '^carson-telemetry' /app/requirements.txt > /tmp/req.txt && \
    pip install --no-cache-dir -r /tmp/req.txt && \
    pip install --no-cache-dir "/app/vendor/carson-telemetry[fastapi]"

COPY app /app/app

EXPOSE 8090
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", "-w", "2", \
     "-b", "0.0.0.0:8090", "--timeout", "120"]
