# Rover Wire Protocol (v1)

This document is the **single source of truth** for how the AI Brain (PC, Python)
and the Robot Body (Arduino, C++) talk to each other. Both sides implement to
_this_ document. It is transport-agnostic: today it runs over USB serial, later
over Wi-Fi, without any change to the messages below.

## Design goals

1. **Human-readable.** Every message is plain ASCII text you can type into a
   serial monitor and read with your eyes. This makes debugging trivial.
2. **Acknowledged, not fire-and-forget.** Every command gets a reply, so the
   Brain always knows whether the Body heard it.
3. **Correlated.** Commands may carry a sequence number; replies echo it, so the
   Brain can match a reply to the command that caused it.
4. **Safe by default.** The Body can emit events on its own — most importantly a
   `HALT` when its safety watchdog stops the motors without being told to.

## Framing

- One message per line, terminated by `\n` (LF).
- Tokens are separated by single spaces.
- Encoding is ASCII.
- A sequence number (`seq`) is an integer in `1..65535`, wrapping around.

## Brain → Body: Commands

A command is: `[seq] VERB [args...]`

The leading `seq` is optional. If the first token is all digits it is the seq;
otherwise the line has no seq.

| Command             | Meaning                                   |
|---------------------|-------------------------------------------|
| `MOVE FWD <cm>`     | Drive forward `<cm>` centimeters          |
| `MOVE BWD <cm>`     | Drive backward `<cm>` centimeters         |
| `TURN LEFT <deg>`   | Turn left `<deg>` degrees (0..360)        |
| `TURN RIGHT <deg>`  | Turn right `<deg>` degrees (0..360)       |
| `STOP`              | Stop all motion immediately               |
| `PING`              | Liveness check / heartbeat                |

Examples:

```
5 MOVE FWD 30      # seq=5, drive forward 30 cm
TURN LEFT 90       # no seq, turn left 90 degrees
STOP
7 PING
```

## Body → Brain: Replies

A reply to a command is: `KIND <seq> [detail]`
The `<seq>` echoes the command's seq, or `-` if the command had none / was
unparseable.

| Reply              | Meaning                                          |
|--------------------|--------------------------------------------------|
| `ACK <seq>`        | Command received and accepted (not yet finished) |
| `DONE <seq>`       | Command completed                                |
| `PONG <seq>`       | Reply to `PING`                                  |
| `ERR <seq> <CODE>` | Command rejected or failed                       |

Error codes: `BADCMD` (could not parse), `BADARG` (bad argument), `BUSY`,
`UNSAFE` (refused for safety). More may be added; codes are single UPPER tokens.

## Body → Brain: Events (unsolicited)

An event is: `EVT KIND [args...]`. Events are not tied to any command.

| Event                    | Meaning                                       |
|--------------------------|-----------------------------------------------|
| `EVT READY`              | Firmware booted and ready                     |
| `EVT SENS <name> <val>`  | Sensor telemetry, e.g. `EVT SENS US 24.5`     |
| `EVT HALT <reason>`      | Body stopped itself, e.g. `EVT HALT WATCHDOG` |
| `EVT LOG <text...>`      | Free-form debug text from the firmware        |

## The safety watchdog (why events exist)

The Body must survive losing the Brain. Two rules the firmware will enforce
(Phase 2+):

1. **Heartbeat timeout.** If the Body hears nothing for `watchdog_timeout_ms`,
   it stops the motors and emits `EVT HALT WATCHDOG`.
2. **Obstacle stop.** If a forward move would collide, it refuses/aborts and
   emits `EVT HALT WATCHDOG` (or `ERR <seq> UNSAFE`).

The Phase 1 `SimulatedTransport` already models rule 2, so Brain-side code can be
written and tested against watchdog behavior before any firmware exists.

## Versioning

This is protocol **v1**. Backward-incompatible changes bump the version and are
recorded here. Additive changes (new events, new error codes) do not.
