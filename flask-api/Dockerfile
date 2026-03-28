FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# first copy the requirements file to leverage Docker cache for dependencies
COPY app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy your application code into the container
COPY app/ .

# Tell Docker this container listens on port 5000
EXPOSE 5000

# Run the app with gunicorn and bind it to all interfaces on port 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "main:app"]