# Safety boundaries

This project is a **closed simulation**. The boundaries below are design
constraints, not just conventions, and should be preserved in any future work.

## What the code does

- Study 1 (`learners/`) trains small numpy neural networks on synthetic
  random bit vectors. The networks only classify; they produce no code, take
  no actions, and touch nothing outside their own arrays. "Reproduction" means
  creating a new array of weights in memory.
- The ecology world (`longrun/`) models an abstract population of agents on
  abstract "nodes" that are plain in-memory Python objects. The agents' entire
  action vocabulary is `CONSUME, REST, REPLICATE, TEST, READ, SHARE, MIGRATE,
  MOVE, STEAL`. Each one only reads or mutates the in-memory simulator state.
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

- **Study 1.** Every run has a fixed number of eras and an exact compute
  budget per era, checked by a test. Populations are fixed at four networks.
- **The ecology world.** Each daily advance runs a fixed number of ticks.
  Population is capped (`max_population` in `longrun/config.json`) and
  limited by finite, regrowing resources.

## Optional LLM agents (not in v0)

If an LLM is later used to control a simulated agent, it is given access only to
the simulator's abstract observation/action API — never to a shell, filesystem,
or network. Its inputs and outputs are logged into the experiment record. An LLM
used to *propose research questions* is kept strictly separate from one used to
*control agents*, so a question-proposing assistant cannot alter the conditions
under which its own hypotheses are tested.
