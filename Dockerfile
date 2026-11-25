FROM python:3.12-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
ENV DB_PATH=/data/pulsegym.db
EXPOSE 5000
CMD ["sh", "-c", "python seed.py && python app.py"]
