# Satellite

A small, dependency-free satellite toolkit: a simulated satellite with its own flight software, a ground station, and a 3D web app that tracks real satellites.

## Run it

Needs Python 3 only. On Windows, double-click `run.bat`. Otherwise, in two terminals:

```bash
python sat.py
python ground.py
```

Then open http://localhost:8000.

## What's inside

| File | What it does |
|------|--------------|
| `sat.py` | Simulated satellite and flight software: orbit, eclipse cycles, battery, solar power, temperature. It switches to SAFE mode on low battery or overtemperature and recovers by itself. Commands: `PING`, `SET_MODE`, `PAYLOAD`, `CLEAR_FAULTS`. One real second is one simulated minute. |
| `ground.py` | Ground station. Talks to `sat.py` over TCP (newline-delimited JSON) and serves the web pages and a small JSON API. |
| `app.html` | 3D globe tracking real satellites from CelesTrak orbit data (stations, GPS, weather, science), with orbit paths, time acceleration and a panel for the simulated satellite. Works on its own if opened directly, but the simulated-satellite panel needs `ground.py`. |
| `dashboard.html` | Telemetry charts, ground track, command buttons and event log for the simulated satellite (`/dashboard.html`). |
| `index.html` | Separate NASA dashboard: live ISS position, Astronomy Picture of the Day and today's near-Earth asteroids. Uses NASA's `DEMO_KEY`, which is rate limited; get a free key at api.nasa.gov. |
| `test_sat.py` | Checks safe-mode entry and recovery: `python test_sat.py` |

## Limits

- The link between satellite and ground has no authentication or encryption.
- Telemetry is not saved to disk.
- There is no attitude model, and the simulated orbit is idealised.
- It is an educational tool, not flight-qualified software. For real missions see NASA cFS and JPL F Prime.

## Ideas for next

- Record telemetry to disk
- Fly the simulated satellite on a real TLE orbit
- Observer view: which satellites pass overhead and when
- Port the flight-software core to Rust for real hardware
