# Back-end build (using a Python image)
FROM python:3.10-slim AS backend

# Set working directory for back-end
WORKDIR /backend

# Install system dependencies for backend
RUN apt-get update && apt-get install -y build-essential

# Copy backend dependencies
COPY ./backend/requirements.txt /backend/
RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt

# Copy backend source code
COPY ./backend/app /backend/app

# Expose the ports used by the back-end and front-end services
EXPOSE 3000 8000

# Set environment variables for back-end
ENV PYTHONUNBUFFERED=1

# Command to start the back-end
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]