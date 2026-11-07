---
name: unity-mlagents-training
description: Use when setting up Unity ML-Agents training of NPC bots on Windows with an RTX 50-series GPU (Unity 6, com.unity.ml-agents 4.x, python mlagents 1.1.0, PyTorch cu128): exact working pins, ONNX export traps, one-process topology for shared experience.
triggers: ml-agents, mlagents, train npc, training bot, onnx, ppo, gail, behavioral cloning, shared policy, huan luyen bot, npc tu hoc
---

# Unity ML-Agents training (verified setup)

## Environment (venv outside the project, e.g. C:\Users\<u>\ml_agents_env_dir\venv, Python 3.10)
1. `pip install "setuptools<81" wheel`
2. `pip install torch --index-url https://download.pytorch.org/whl/cu128` (RTX 5070/Blackwell needs CUDA 12.8+; check `torch.cuda.is_available()`).
3. `pip install mlagents==1.1.0` (pairs with Unity package com.unity.ml-agents 4.2.0: handshake logs `communication version 1.5.0`).
4. ONNX export with torch 2.11 needs `onnxscript` AND `onnx`, but a plain `pip install onnxscript onnx` upgrades protobuf to 7.x and BREAKS mlagents ("Descriptors cannot be created directly"). Fix: `pip install "protobuf==3.20.3" "onnx==1.17.0" "numpy<2"`. pip then prints conflicts with mlagents' numpy/onnx pins; they are harmless, verify with a real export.
5. Set `PYTHONUTF8=1` (and `PYTHONIOENCODING=utf-8`): the torch exporter prints emoji and crashes on the cp1252 console. Verify with a tiny `torch.onnx.export(...opset_version=15)`.
- Without step 4-5 training runs fine and then dies at the first checkpoint save (no ONNX, no deployable model). Test the export BEFORE a long run.

## Run
- `mlagents-learn config.yaml --run-id X --force --time-scale 5 --results-dir <git-ignored> --timeout-wait 300`, then press Play in the Editor (the Editor is the environment). Changing C# scripts during Play triggers a domain reload and kills the run.
- Agent: BehaviorParameters name must equal the YAML behavior key; observation size and action spec must match the code (const in the Agent).
- Idle agent shows mean reward = time penalty x MaxStep (about -10 for 0.001 x 10000): normal at the start.

## Topology for cooperative NPCs with shared experience
- A trainer talks to ONE Unity process. Agents with the same BehaviorName in that process share one policy and every agent's experience updates it. So both partners must be agents in the SAME process.
- A static global input channel (touch input) blocks two agents per process: give each player an input source object, and let the server drive NPC players (server-owned, no client connection). The same design later spawns NPC partners in production when no human is online.
- Never train or accept with a solo player when the game is 2-player co-op.
