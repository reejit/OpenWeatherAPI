# Use an official Python runtime as a parent image
FROM python:3.6.8
# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1
# Set the working directory to /code
WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
