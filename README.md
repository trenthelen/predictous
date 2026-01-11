# Predictous

> **Alpha (v0.1)** - Early development, expect rough edges.

Open-source forecasting system built on [Bittensor Subnet 6: Numinous](https://numinouslabs.io/). Submit prediction questions and get probability estimates from top-ranked AI agents on the network.

## Features

- **Sandboxed Execution** - Agents run in isolated Docker containers with memory, CPU, and timeout limits
- **Cost Control** - Per-agent budgets ($0.02 LLM, $0.10 search), global daily budget, and per-IP rate limits
- **Concurrent Request Limits** - Max 2 active requests per IP to prevent resource hogging
- **Prediction Modes** - Champion (top agent), Council (top 3 averaged), or Selected (specific agent)
- **Shareable Predictions** - Each prediction gets a unique URL for sharing
- **History** - Users can view their past predictions

## Prerequisites

1. **Numinous Gateway** - Clone and run the official gateway from [numinouslabs/numinous](https://github.com/numinouslabs/numinous). You'll need your own Chutes and Desearch API keys.

2. **Docker** - Must be installed and your user must be in the `docker` group:
   ```bash
   sudo usermod -aG docker $USER
   # Log out and back in for changes to take effect
   ```

## Backend Setup

```bash
cd backend

# Create virtual environment (using venv or uv)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (GATEWAY_URL is required)

# Run
python -m server.app
```

The backend runs on `http://localhost:8080` by default.

See [backend/README.md](backend/README.md) for module documentation.

## Frontend Setup

```bash
cd frontend

npm install

# Development
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` to the backend.

See [frontend/README.md](frontend/README.md) for further documentation.

## Running Locally

1. Start the Numinous gateway:
   ```bash
   cd numinous
   source .venv/bin/activate
   numi gateway start
   ```

2. Start the backend (in its own terminal):
   ```bash
   cd backend
   source .venv/bin/activate
   python -m server.app
   ```

3. Start the frontend dev server (in its own terminal):
   ```bash
   cd frontend
   npm run dev
   ```

Open `http://localhost:5173` in your browser.

## Production Deployment

For self-hosting with HTTPS:

1. **Build frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Generate SSL certificates** (or use certbot):
   ```bash
   ./nginx/generate-certs.sh
   ```

3. **Start the gateway and backend** using systemd, pm2, or similar.

4. **Start nginx** (routes both frontend and API):
   ```bash
   docker compose up -d
   ```

The app will be available on ports 80 (redirects to 443) and 443.
