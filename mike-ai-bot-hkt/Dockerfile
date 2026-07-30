FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py knowledge.txt partners.py buttons.py topics.py stats_report.py topic_labels.py ./
COPY admin_api/ admin_api/
COPY db/ db/
COPY scripts/ scripts/
COPY media/ media/

CMD ["python", "bot.py"]
