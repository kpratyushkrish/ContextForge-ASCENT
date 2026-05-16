FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir numpy>=1.24.0

WORKDIR /app

ENTRYPOINT ["python"]
CMD ["run.py", "--adapter", "adapters.myteam:Engine", "--out", "outputs/l3_report.json"]
