echo "Starting backend..."
python3 backend/backend.py &

sleep 5

echo "Starting frontend..."
cd webapp
npm run dev