# Rover

An AI-powered autonomous mobile assistant built from an RC car chassis, an
Arduino, and a PC-based AI brain. Rover senses its surroundings, makes decisions,
and physically acts — the goal is a genuinely useful mobile robot, not a demo.

> Status: **Phase 1 — Software Foundation & Simulation.** The Brain can drive a
> simulated Body end-to-end (commands, acknowledgements, telemetry, and the
> safety watchdog) with zero hardware.

## Architecture in one picture

```
  AI BRAIN (PC, Python)                    ROBOT BODY (Arduino, C++)
  perception / decision / nav              motors / sensors / safety watchdog
            |                                        ^
            |  Command objects                       |  real-time control
            v                                        |
        RoverLink  --encode-->  Transport  --bytes-->  firmware
                   <-decode--   (serial/wifi/sim)   <-- replies & events
```

The **Transport** is a swappable seam: a `SimulatedTransport` today, USB serial
in Phase 2, Wi-Fi in Phase 6 — the Brain code above it never changes. The
messages that cross it are specified once in [`docs/protocol.md`](docs/protocol.md),
and both the Python and (future) Arduino sides implement to that spec.

See [`docs/architecture.md`](docs/architecture.md) for the full design and
[`docs/roadmap.md`](docs/roadmap.md) for the plan.

## Quick start

```bash
# 1. (optional) create a virtual environment, then install the package + dev deps
pip install -r requirements-dev.txt
pip install -e .

# 2. run the test suite (no hardware required)
python -m pytest

# 3. watch the Brain drive a simulated Rover into a wall (and stop itself)
python examples/hello_rover.py
```

## Project layout

```
rover/            # the AI Brain (Python package)
  protocol/       # wire-protocol message model + codec  (the contract)
  transport/      # byte-level links: base interface + simulator
  link.py         # RoverLink: message-level API over any transport
  config/         # central configuration
firmware/         # Arduino C++ (the Body) — arrives in Phase 2
docs/             # architecture, protocol spec, roadmap
examples/         # runnable demos
tests/            # unit (protocol) + integration (brain <-> simulated body)
```

## Principles

- **No fake functionality.** Simulated components implement the *same* interface
  real hardware will; the code above them can't tell the difference.
- **No paid services.** Open-source and local only (OpenCV, PySerial, Ollama).
- **Safe by design.** The Body can stop itself; the Brain is never a single point
  of failure for physical safety.
- **Maintainable for years.** Small modules, clear seams, tests, and docs.
