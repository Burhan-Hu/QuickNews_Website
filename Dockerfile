FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY app/package*.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for lxml
RUN apt-get update && apt-get install -y \
    libxml2-dev libxslt1-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY news_dashboard/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt lxml
COPY news_dashboard/ ./news_dashboard/
COPY --from=frontend-builder /app/dist ./news_dashboard/static/
ENV FLASK_APP=news_dashboard/ir/xml_api.py
EXPOSE 5000
CMD ["python", "news_dashboard/main.py"]
