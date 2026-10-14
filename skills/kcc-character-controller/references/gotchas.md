# KCC gotchas (DATA)

From report 04 (VERIFIED in code/assets):
1. `_orientationSharpness` (10) only gates > 0; the real turn uses a hard-coded `1 - exp(-100 dt)`. Copy the 100 and delete the dead field.
2. Coyote and jump buffer are 0.5 s each (default KCC practice is ~0.1). It feels forgiving; make it a profile value.
3. `Ladder` keeps a static `Dictionary<Collider, Ladder>`; it is not reset on domain reload. Add a `RuntimeInitializeOnLoadMethod(SubsystemRegistration)` reset.
4. Bottom camera orbit is overridden at runtime (`Factory_Camera._bottomRigNormal` (-5, 1)) while the prefab stores (-1, 3); read both before tuning.
5. `AirSteeringSpeedPoints` (angle -> factor) reduces air steering against the current motion; easy to forget when porting.
6. KT setters mutate the singleton `Factory_CharacterKC` at runtime; use profiles/layers instead (ME does).
7. ME Escape and Obby profiles differ only by a x1.5 scalar: derive one from the other.
8. Release of a pooled object or a Kill from a physics callback must not destroy immediately (`pool-everything`).
9. The nav agent body must be overwritten from the KCC motor each LateUpdate or it fights the controller (`bot-brain-waypoints`).
10. Not verified: Fixed Timestep value, KCC interpolation settings, the Cinemachine Y-axis start value.
