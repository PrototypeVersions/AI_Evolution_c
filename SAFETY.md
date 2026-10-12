# Safety boundaries

This project is a **closed simulation**. The boundaries below are design
constraints, not just conventions, and should be preserved in any future work.

## What the code does

- Models an abstract population of agents on abstract "nodes" that are plain
  in-memory Python objects.
- In the study engine (`sim/`), the agents' entire action vocabulary is `OBSERVE, MOVE, TEST, REPLICATE,
  RECORD, WAIT`; in the long run (`longrun/`) it is `CONSUME, REST, REPLICATE,
  TEST, READ, SHARE, MIGRATE, MOVE, STEAL`. Each one only reads or mutates the
  in-memory simulator state.
- `REPLICATE(node)` appends a new agent record to a Python list. Nothing is
  installed, copied, or started anywhere.
- In the long-run world, `MIGRATE` and `MOVE` change which in-memory habitat
  or node an agent record points to. Habitats are simulated regions, not
  machines, and the long run will not be extended to run agents across real
  or volunteer computers.

## What the code does not do, and must not be extended to do

- **No networking.** The simulation imports no socket/HTTP/SSH libraries and
  makes no outbound connections. Device discovery, scanning, and propagation
  across real machines are explicitly out of scope.
- **No real targets.** There is no concept of a real IP, host, port, or device
  anywhere in the model.
- **No exploitation or persistence.** Nothing in the model represents gaining
  access to, or persisting on, a system that exists outside the simulator.

## Enforced limits

Every run is bounded by hard caps (see `sim/engine.py`): a maximum population,
a maximum number of steps, and a maximum wall-clock budget. A run that hits a
cap stops and is recorded as capped, so a configuration cannot expand without
limit.

## Optional LLM agents (not in v0)

If an LLM is later used to control a simulated agent, it is given access only to
the simulator's abstract observation/action API — never to a shell, filesystem,
or network. Its inputs and outputs are logged into the experiment record. An LLM
used to *propose research questions* is kept strictly separate from one used to
*control agents*, so a question-proposing assistant cannot alter the conditions
under which its own hypotheses are tested.
