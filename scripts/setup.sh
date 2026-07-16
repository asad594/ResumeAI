#!/bin/bash
echo "Starting AI Resume Analyzer..."

echo "Building Docker containers..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for database..."
sleep 5

echo "Running migrations..."
docker-compose exec backend alembic upgrade head

echo "Application is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000/api/v1/docs"
