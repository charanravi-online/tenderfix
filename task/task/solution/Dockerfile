FROM python:3.9-slim

WORKDIR /app

# Copy only the requirements.txt first to leverage Docker cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application files
COPY . /app

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5000"]
