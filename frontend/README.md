# Predictous Frontend

React frontend for the prediction service.

## Quick Start

```bash
npm install
npm run dev      # http://localhost:5173
```

Backend must be running at `localhost:8080` (proxied via Vite).

## Stack

- React 18 + TypeScript
- Tailwind CSS v4
- Vite

## Structure

```
src/
├── api/client.ts       # API calls
├── components/         # React components
├── hooks/              # useTheme, useAgents, usePrediction, useHealth
├── types/              # TypeScript types
└── utils/format.ts     # Formatting helpers
```

## API Proxy

Dev server proxies `/api/*` to `localhost:8080` with 5-minute timeout (predictions are slow).

To use a different backend:
```bash
VITE_API_URL=https://api.example.com npm run dev
```

## Build

```bash
npm run build    # outputs to dist/
```
