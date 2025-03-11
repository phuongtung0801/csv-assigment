# Dockerfile
FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Đặt working directory đến thư mục chứa code
WORKDIR /app/csvapi-django

# Copy file requirements và cài đặt dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . /app/

# Chạy Gunicorn để phục vụ ứng dụng Django
CMD ["gunicorn", "csvapi.wsgi:application", "--bind", "0.0.0.0:8000"]
