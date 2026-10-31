# NEXUS // AQUARIUM

An evolving artificial marine ecosystem with one authoritative Python simulation shared by terminal and browser renderers.

## Phase 3–5 foundation
- Genetics: quantitative heritable traits, mutation and generation tracking.
- Behaviour: nine sensory channels, bounded memory, learning primitives, schooling and predator avoidance.
- Ecology: water chemistry, trophic-link data, metabolism, mortality, generic reproduction and disturbances.
- Backend: standard-library HTTP server with authenticated snapshots, pause/resume, fixed-step and disturbance controls.
- Browser: GitHub Pages renderer connects to the same backend; Pages does not host or run Python.

This is an early extensible model, not a complete scientific ecosystem. Species-specific reproductive biology, broad species coverage, complete nutrient cycling, full SPH fluid simulation, advanced social cognition, robust WebSocket transport and production deployment hardening remain future work.

## Run backend
Python 3.10+; standard library only.

```sh
export NEXUS_API_TOKEN="use-a-random-secret-at-least-16-characters"
python3 backend.py --host 0.0.0.0 --port 8765
```

The service exposes `GET /health`, authenticated `GET /snapshot`, and authenticated `POST /control/pause`, `/control/step`, `/control/disturbance`. Send `Authorization: Bearer <token>`. Do not expose the prototype HTTP server directly to the public internet; use TLS, a private VPN or authenticated reverse proxy, and restrict CORS to the exact Pages origin before public use. Never commit the bearer token.

## GitHub Pages
Pages serves this static browser UI. Run the Python backend on a reachable machine and enter its URL and token in the page. A static Pages URL alone is not a live backend. Browser connection requires HTTPS for remote sites; plain HTTP on a remote host will be blocked as mixed content. For local Termux use, the backend and browser must share a reachable network and a secure access path.
