# Cinemachine v2 vs v3 mapping

Status: the v2 column was verified against the reference project. The v3 column comes from public Cinemachine 3 documentation and was NOT run or compiled against an installed v3 package (the studio's current project pins 2.10.7). Check the installed package source before copying a v3 line.

| Concept | v2 (`Cinemachine`) | v3 (`Unity.Cinemachine`) |
|---|---|---|
| Virtual camera | `CinemachineVirtualCamera` | `CinemachineCamera` |
| Three-ring orbit camera | `CinemachineFreeLook` (3 rig children) | `CinemachineCamera` + `CinemachineOrbitalFollow` (OrbitStyle ThreeRing, Orbits top/center/bottom height + radius) |
| Follow offset / binding | `CinemachineTransposer` (BindingMode, FollowOffset, damping) | tracker settings on `CinemachineOrbitalFollow` (BindingMode incl. SimpleFollowWithWorldUp, positional damping) |
| Aim | `CinemachineComposer` (ScreenX/Y, dead/soft zone) | `CinemachineRotationComposer` (screen position, dead zone, hard limits). One composer for the camera: a different ScreenY per rig has no direct equivalent; approximate with the target offset |
| Input | write `m_XAxis.m_InputAxisValue` / `m_YAxis.m_InputAxisValue` | `CinemachineInputAxisController` (or set the horizontal/vertical axis value from your input code) |
| Collision | `CinemachineCollider` | `CinemachineDeoccluder` |
| Noise | `CinemachineBasicMultiChannelPerlin` (`m_AmplitudeGain`, `m_FrequencyGain`) | `CinemachineBasicMultiChannelPerlin` (`AmplitudeGain`, `FrequencyGain`) |
| Lens | `vcam.m_Lens.FieldOfView / NearClipPlane / FarClipPlane` | `vcam.Lens.FieldOfView / NearClipPlane / FarClipPlane` |
| Priority | `vcam.Priority` (int) | `vcam.Priority.Value` (priority settings) |
| Brain blend | `brain.m_DefaultBlend` | `brain.DefaultBlend` |
| Warp | `ForceCameraPosition(pos, rot)` | `ForceCameraPosition(pos, rot)` |
| Editor MCP tools | v2 tools | v3 tools; the Editor MCP Cinemachine extension must match the generation |

Rules
1. Detect the major version first (`manifest.json` and `using` lines). One generation per project.
2. API-independent recipe values stay: FOV 40, near 0.75, far 500, orbits (6,1)/(3,6)/(-1,3), zero damping, ForceCameraPosition one frame after the reset event, FOV on the lens, one Brain, nested camera prefab.
3. Migration v2 to v3 is a task of its own (Unity ships an upgrade tool); never run it as a side effect.
4. After any version change re-verify: Brain count, FOV/far on the lens, shake gain returns to 0, respawn warp.
