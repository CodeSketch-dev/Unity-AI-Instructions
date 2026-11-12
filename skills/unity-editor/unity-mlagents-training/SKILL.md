---
name: unity-mlagents-training
description: "Use when setting up Unity ML-Agents training of NPC bots on Windows with an RTX 50-series GPU (Unity 6, com.unity.ml-agents 4.x, python mlagents 1.1.0, PyTorch cu128): exact working pins, ONNX export traps, one-process topology for shared experience."
triggers: ml-agents, mlagents, train npc, training bot, onnx, ppo, gail, behavioral cloning, shared policy, huan luyen bot, npc tu hoc
---

# Unity ML-Agents training (verified setup)

## Environment (venv outside the project, e.g. C:\Users\<u>\ml_agents_env_dir\venv, Python 3.10)
1. `pip install "setuptools<81" wheel`
2. `pip install torch --index-url https://download.pytorch.org/whl/cu128` (RTX 5070/Blackwell needs CUDA 12.8+; check `torch.cuda.is_available()`).
3. `pip install mlagents==1.1.0` (pairs with Unity package com.unity.ml-agents 4.2.0: handshake logs `communication version 1.5.0`).
4. Do NOT `pip install onnxscript`: it drags protobuf 7 (breaks mlagents: "Descriptors cannot be created directly") and numpy>=1.26 / ml_dtypes>=0.6 (mlagents needs `numpy<1.24`, `np.float` is gone in newer numpy). Working pins: `pip install "protobuf==3.20.3" "numpy==1.23.5"`.
5. torch>=2.9 `torch.onnx.export` defaults to the dynamo exporter (needs onnxscript). Use the legacy exporter instead: patch `site-packages/mlagents/trainers/torch_entities/model_serialization.py` and add `dynamo=False` to the `torch.onnx.export(...)` call (keep a `.orig` copy). Verify with a tiny `torch.onnx.export(..., opset_version=15, dynamo=False)`. Set `PYTHONUTF8=1` anyway (the exporter prints emoji and crashes on a cp1252 console).
6. Validate configs through the real path, not `RunOptions.from_dict`: `from mlagents.trainers.learn import parse_command_line; parse_command_line([cfg, "--run-id", "x", "--force"])` (trainer types register there).
- Without step 4-6 training runs fine and then dies at the first checkpoint save (no ONNX, no deployable model). Test the export BEFORE a long run.

## Run
- `mlagents-learn config.yaml --run-id X --force --time-scale 5 --results-dir <git-ignored> --timeout-wait 300`, then press Play in the Editor (the Editor is the environment). Changing C# scripts during Play triggers a domain reload and kills the run.
- Agent: BehaviorParameters name must equal the YAML behavior key; observation size and action spec must match the code (const in the Agent).
- Idle agent shows mean reward = time penalty x MaxStep (about -10 for 0.001 x 10000): normal at the start.

## Topology for cooperative NPCs with shared experience
- A trainer talks to ONE Unity process. Agents with the same BehaviorName in that process share one policy and every agent's experience updates it. So both partners must be agents in the SAME process.
- A static global input channel (touch input) blocks two agents per process: give each player an input source object, and let the server drive NPC players (server-owned, no client connection). The same design later spawns NPC partners in production when no human is online.
- Never train or accept with a solo player when the game is 2-player co-op.

## Lessons from a long unattended NPC run (evidence-backed)
- Owner intent decides the method: if the owner wants the NPC to LEARN, never put a scripted teacher, baked route or hand rules in the policy path (they called that "imposing rules"). Start pure PPO (+ RND curiosity) with reward only; add help (curriculum start distance, route observations, demos) only after measuring that pure RL stalls, and say so. A shipped NPC is just the exported ONNX policy run by plain C#, never an LLM.
- Editor training is slow (~50-65 steps/s even at time-scale 20). For real throughput build a standalone player and run `--env <exe> --num-envs N --no-graphics` with a per-instance port (derive from `--mlagents-port`). Judge progress only from `Mean Reward` lines in the trainer log (`grep "Mean Reward"`), not from the Editor.
- Anything that sets `Time.timeScale` (slow-mo on events like glass breaks) silently kills the trainer's time-scale: restore the previous value, not 1.
- Ownerless server-driven NPCs need server-side setup that an owner would do by RPC (e.g. skin index SyncVar defaulting to -1 gave invisible characters). Check a screenshot, not a component count.
- Editing C# during Play/training forces a domain reload and drops the run: kill the trainer first, restart it after compile, then press Play.
- Put reward/penalty for repeated failure (falls, breaking the shared object at the same spot) in the design; log best checkpoint reached so the morning report is honest.
