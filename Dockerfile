FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY requirements.txt /code/
COPY requirements-dev.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install -r requirements-dev.txt
COPY . /code/ 