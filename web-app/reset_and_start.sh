#!/bin/bash
set -e

echo "🛑 Stopping containers..."
docker-compose down

echo "🗑️  Removing old database..."
rm -f backend/data/web_app.db

echo "🚀 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 15

echo "🌱 Seeding conversation data..."
docker-compose exec -T web-app-backend python seed_data.py

echo "✅ Setup complete!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo ""
echo "To view database:"
echo "  sqlite3 backend/data/web_app.db"