FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files during build
RUN python manage.py collectstatic --noinput

# Default command runs gunicorn in production
CMD ["gunicorn", "ExtraPaints.wsgi:application", "--bind", "0.0.0.0:8000"]
