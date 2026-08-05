# Rover Roadmap

Each phase produces something that works and is verified before the next begins.
We never build on unproven foundations, and we lock in safety before motion.

Legend: ✅ done · 🔶 in progress · ⬜ not started

## Phase 1 — Software Foundation & Simulation  🔶
Goal: a testable Brain that drives a simulated Body, no hardware.
- ✅ Repo skeleton, packaging, test harness
- ✅ Protocol spec (`docs/protocol.md`) — the source of truth
- ✅ Protocol message model + codec, with unit tests
- ✅ `Transport` interface + `SimulatedTransport` (incl. obstacle watchdog)
- ✅ `RoverLink` message-level API + integration tests
- ✅ Config module, runnable `examples/hello_rover.py`
- ⬜ (next) A minimal Brain control loop that reacts to telemetry

## Phase 2 — Arduino Communication  ⬜
Goal: a real serial link, Brain ↔ Arduino.
- Firmware serial loop + `CommandParser` implementing `docs/protocol.md`
- `SerialTransport` (pyserial) implementing the `Transport` interface
- ACK / heartbeat / **watchdog timeout** in firmware
- Round-trip verified with an LED as a motor proxy
- Hardware: Arduino only

## Phase 3 — Motor Control  ⬜
Goal: Rover physically moves on command.
- `MotorDriver` (L293D) + `MotionController` firmware
- Calibration tools (cm-per-step, turn degrees)
- `MOVE` / `TURN` / `STOP` verified on the chassis
- Hardware: chassis, motors, L293D, battery

## Phase 4 — Sensors & Autonomy  ⬜
Goal: Rover senses and avoids obstacles on its own.
- `SensorReader` (ultrasonic) + telemetry stream (`EVT SENS`)
- Servo scanning; reactive obstacle avoidance
- Hardware: HC-SR04 ultrasonic, servo

## Phase 5 — Computer Vision & AI  ⬜
Goal: Rover understands what it sees and hears.
- OpenCV perception pipeline; object detection
- Ollama reasoning layer (fast `llama3.2:3b` + `gpt-oss:20b`) behind one interface
- Perception → decision loop
- Hardware: camera

## Phase 6 — Wireless Communication  ⬜
Goal: cut the USB cord.
- `WifiTransport` behind the existing `Transport` interface (logic unchanged)
- Hardware: ESP32 or a Raspberry Pi bridge

## Phase 7 — Advanced Assistant Capabilities  ⬜
Goal: real usefulness.
- Object carrying, space monitoring, voice commands, task routines
- Path toward onboard compute
