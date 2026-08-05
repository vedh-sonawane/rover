# Rover Architecture

## Two layers, split at their natural fault line

Rover has two kinds of work with fundamentally different requirements:

| Concern                         | Nature                    | Latency budget | Failure cost        |
|---------------------------------|---------------------------|----------------|---------------------|
| Motor pulses, sensor timing     | Hard real-time            | µs–ms          | Physical crash      |
| Vision, planning, reasoning     | Soft real-time, compute   | 100 ms–s       | Slow, but safe      |

An Arduino UNO R3 (16 MHz, 2 KB RAM) is excellent at the first and incapable of
the second; a PC is the opposite. So we split there:

- **Robot Body** (Arduino, C++): motors, sensors, low-level control, and an
  autonomous safety watchdog. The Body must stay safe even with no Brain.
- **AI Brain** (PC, Python): perception, decisions, navigation, reasoning. It
  sends *high-level* commands and reacts to telemetry.

The Arduino is **not** the AI. It is the reliable, real-time body.

## The seam: Transport + Protocol

Everything crosses one well-defined boundary:

```
Brain logic
   │  Command / Response / Event  (rover.protocol.messages)
   ▼
RoverLink            adds sequence numbers, correlates replies
   │  bytes          (rover.protocol.codec encodes/decodes)
   ▼
Transport            moves bytes only, knows nothing of the protocol
   │
   ▼
SimulatedTransport (Phase 1) → SerialTransport (Phase 2) → WifiTransport (Phase 6)
```

Two independent abstractions, deliberately:

- **Protocol** (`rover/protocol/`): the *language*. One text-based, line-oriented,
  acknowledged message set, specified in `docs/protocol.md`. Both the Brain and
  the Arduino firmware implement to that spec, so they can be built separately.
- **Transport** (`rover/transport/`): the *pipe*. A four-method byte interface
  (`open/close/write/read_line`). Swapping serial for Wi-Fi swaps only this.

Because these are separate, changing the pipe never changes the language, and
changing the language never touches the Brain's logic.

## Why a simulator, not a mock of results

`SimulatedTransport` implements the real `Transport` byte interface and speaks
the real protocol. It maintains a little virtual world state (distance ahead) and
responds the way the firmware will — including refusing to drive into an obstacle
and emitting `EVT HALT WATCHDOG`. This is the difference between *simulating a
component behind its real interface* (allowed, valuable) and *faking a result*
(forbidden): Brain code written and tested against the simulator runs unchanged
against real hardware.

## Safety model

Physical safety is a Body responsibility, never solely the Brain's:

1. **Heartbeat watchdog** (Phase 2 firmware): no message for
   `watchdog_timeout_ms` → stop motors, emit `EVT HALT WATCHDOG`. A Brain crash
   or Wi-Fi drop can never leave a powered robot driving blind.
2. **Obstacle watchdog** (already simulated in Phase 1): a forward move that
   would collide is refused.

## Reasoning layer (Phase 5, designed now)

Two local Ollama models behind one interface, mirroring the reactive/deliberative
split of the hardware:

- **Fast model** (`llama3.2:3b`): the low-latency command→intent loop.
- **Reasoning model** (`gpt-oss:20b`): heavier multi-step planning, called only
  when needed.

Both are configured in `rover/config/settings.py` and will sit behind a single
`reasoning` interface so the model choice stays swappable.

## Directory responsibilities

| Path                | Responsibility                                        |
|---------------------|-------------------------------------------------------|
| `rover/protocol/`   | Message model + codec (the contract). No I/O.         |
| `rover/transport/`  | Byte-level links. `base.py` = interface; `simulated.py`.|
| `rover/link.py`     | `RoverLink`: message-level API, sequence numbers.     |
| `rover/config/`     | Central configuration + env overrides.                |
| `firmware/`         | Arduino C++ (Phase 2+).                                |
| `tests/`            | `unit/` protocol, `integration/` brain↔simulated body.|
