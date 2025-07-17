FROM python:3.10-slim

WORKDIR /backend_app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python3", "main.py" ]