# Use the official Rasa image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy all project files
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose the Rasa server port
EXPOSE 5005


