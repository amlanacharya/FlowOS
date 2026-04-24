#!/bin/bash
# Health check script for FlowOS backend

echo "🏥 FlowOS Health Check"
echo "====================="

# Check if app is running
echo -n "App health... "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗ (app not responding on :8000)"
    exit 1
fi

# Check if database is responding
echo -n "Database health... "
docker-compose exec -T db pg_isready -U flowos > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓"
else
    echo "✗ (database not responding)"
    exit 1
fi

# Try API endpoint
echo -n "API health... "
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗ (OpenAPI docs not available)"
    exit 1
fi

echo ""
echo "✅ All systems operational!"
echo ""
echo "API Docs: http://localhost:8000/docs"
echo "Health:   http://localhost:8000/health"
