#!/bin/bash
echo "Starting development environment..."

docker-compose up -d db

echo "Waiting for database..."
sleep 3

echo "Starting backend..."
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "Development servers started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/v1/docs"

wait $BACKEND_PID $FRONTEND_PID
