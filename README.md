# Jac Agent Civilization Simulator

Local-first hackathon MVP for a civilization of autonomous agents. The backend runs deterministic simulation ticks and calls Ollama only for selected diplomacy/strategy moments. The frontend renders the live world, agent memory, relationships, reasoning logs, and disaster timeline.

## Run Backend

```powershell
cd D:\Games\CIVILIZATION
pip install -r backend\requirements.txt
$env:PYTHONPATH="D:\Games\CIVILIZATION\backend"
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8001
```

## Run Frontend

```powershell
cd D:\Games\CIVILIZATION\frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Test

```powershell
cd D:\Games\CIVILIZATION
$env:PYTHONPATH="D:\Games\CIVILIZATION\backend"
python -m pytest backend\tests -q
cd frontend
npm run build
```

## Notes

- If Ollama is running at `http://localhost:11434`, diplomacy events can use the configured local model.
- If Ollama is unavailable, the simulator records a fallback reasoning log and continues.
- Normal movement, hunger, resource collection, trade, memory, and disaster response are rule-based.
