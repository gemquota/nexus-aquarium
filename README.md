# NEXUS // AQUARIUM

A prototype artificial marine ecosystem with one authoritative Python simulation shared by terminal and browser renderers.

## Current backend
- Python standard-library HTTP service; no runtime dependencies.
- Authenticated snapshots and controls.
- Configurable Koyeb `PORT` and bind address.
- CORS restricted to `NEXUS_ALLOWED_ORIGIN` (defaults to the GitHub Pages origin).
- Atomic JSON checkpoints, restored on startup.
- Coral reef condition model: bleaching stress, recovery, calcification and live dashboard telemetry (simplified educational proxy, not a calibrated forecast).
- Bearer token compared in constant time; request body size limited.

This is an early extensible model, not a complete scientific ecosystem. Species-specific reproductive biology, broad species coverage, complete nutrient cycling, full SPH fluid simulation, advanced social cognition and production-grade observability remain future work.

## Run locally
```sh
export NEXUS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export NEXUS_ALLOWED_ORIGIN="https://gemquota.github.io"
export NEXUS_STATE_FILE="./data/nexus-state.json"
python3 backend.py
```

Endpoints: `GET /health`, authenticated `GET /snapshot`, authenticated `POST /control/pause`, `/control/step`, and `/control/disturbance`. Send `Authorization: Bearer <token>`.

## Deploy on Koyeb
1. Sign in to Koyeb and connect GitHub.
2. Create App → Web Service → GitHub → `gemquota/nexus-aquarium`, branch `main`.
3. Select **Dockerfile** as the builder and choose the **Free** instance.
4. Set environment variables:
   - `NEXUS_API_TOKEN`: generate a long random secret locally; never commit it.
   - `NEXUS_ALLOWED_ORIGIN`: `https://gemquota.github.io`
   - `NEXUS_STATE_FILE`: `/data/nexus-state.json`
5. Deploy. Koyeb supplies `PORT`; the container listens on it.
6. Copy the service's `https://…koyeb.app` URL into the dashboard, then enter the same token.

### Free-tier persistence warning
Koyeb's Free Instance has no persistent volumes and scales to zero after one hour without traffic. The JSON checkpoint protects against process restarts while the container filesystem remains available, but **it is not durable storage across scale-to-zero, instance replacement or redeployment**. Do not treat it as a reliable long-term aquarium save. To guarantee persistence, attach a paid persistent volume or add an external database/object store and configure its credentials as secrets. The free Koyeb PostgreSQL allowance is limited and is not suitable as an always-on database.

### Security
- Keep `NEXUS_API_TOKEN` private. Do not paste it into source code, issues, screenshots or public chat.
- The dashboard sends the token from the password field in browser memory; use a private browser/device and do not share the dashboard session.
- CORS is an origin restriction, not authentication. Bearer authentication remains required for snapshots and controls.
- Only the Pages origin is allowed by default. If hosting the dashboard elsewhere, change the exact origin.
- Do not enable public debug endpoints or log authorization headers.

## Dashboard
[Open the GitHub Pages dashboard](https://gemquota.github.io/nexus-aquarium/). Pages serves the UI only; Koyeb runs the Python API.

## Side-view sprite library

See [`assets/sprites/README.md`](assets/sprites/README.md) for the side-view asset plan, vetted sprite packs, licence notes and safe local import instructions. The source catalogue is [`assets/sprites/sources.json`](assets/sprites/sources.json). Third-party binaries are not included until their licence permits public redistribution or they are provided through an appropriately licensed private asset host.
