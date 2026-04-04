FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY app/package*.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY news_dashboard/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY news_dashboard/ ./news_dashboard/
COPY --from=frontend-builder /app/dist ./news_dashboard/ir/static/
ENV FLASK_APP=news_dashboard/ir/xml_api.py
EXPOSE 5000
CMD ["python", "news_dashboard/main.py"]
