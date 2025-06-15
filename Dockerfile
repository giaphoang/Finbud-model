# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    make \
    curl \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy poetry configuration files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --without superlinked_rag --no-interaction --no-ansi -v

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
# Add src directory to Python path
ENV PYTHONPATH=/app/src

# Expose the port the app runs on
EXPOSE ${PORT}

# Create a shell script to run the application
RUN echo '#!/bin/sh\npoetry run uvicorn src.backend.api.main:app --host 0.0.0.0 --port $PORT' > /app/start.sh && \
    chmod +x /app/start.sh

# Start the FastAPI app using Uvicorn
CMD ["/app/start.sh"]