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

# Expose the port the app runs on
EXPOSE 8000

# Set PYTHONPATH so modules like 'core' can be found
ENV PYTHONPATH=/app/src

# Command to run the application
CMD ["poetry", "run", "python", "src/backend/api/main.py"] 