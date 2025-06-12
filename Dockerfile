# Use Python 3.10 as base image
FROM python:3.10-slim

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
COPY pyproject.toml ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Generate lock file and install dependencies
RUN poetry lock && \
    poetry install --without dev --no-interaction --no-ansi -v --no-root

# Copy the rest of the application
COPY . .

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["poetry", "run", "uvicorn", "src.backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"] 