---
name: state-machine-template
description: Build a runtime mode with the framework StateMachine and IStateMachine state classes. Use for AI, game phases or character modes instead of boolean flag soup.
---

# State machine template

Owner pattern (knife-tower `AI.cs`, report 01, VERIFIED):
```csharp
StateMachine<AI_State> _sm;
void InitStateMachine()
{
    _sm = new StateMachine<AI_State>();
    _sm.AddState(AI_State.Idle, new AI_State_Idle(this));   // class AI_State_Idle : IStateMachine, ctor(owner)
    _sm.AddState(AI_State.Stop);                            // empty state
    _sm.CurrentState = AI_State.Stop;                       // set initial state explicitly
}
void Update() => _sm?.Update();
void FixedUpdate() => _sm?.FixedUpdate();
void OnDestroy() => _sm?.Dispose();
public AI_State State { get => _sm.CurrentState; set => _sm.CurrentState = value; }
```
States live in `Logic/<Feature>/State/<Feature>_State_<Name>.cs`; implement `Init, OnStart, OnUpdate, OnFixedUpdate, OnStop, OnDestroy`. All transitions go through the one `State` property.

## Gotchas (VERIFIED in package code)
- The `CurrentState` getter throws before the first assignment.
- `PreviousState` is never set (always equals current): do not rely on it; track it yourself.
- Unregistered label -> `KeyNotFoundException`. Transition to the same state re-runs stop/start.
- It is not a MonoBehaviour: the owner must forward `Update`/`FixedUpdate` and call `Dispose()` in `OnDestroy`.
- `AddState` calls `Init()` immediately.

## Added from open-project-1 (2026-11-02)
Source: third-party example (Unity open-project-1, Apache-2.0), IDEA-ONLY.
- Its designer-authored SO state machine (State = actions + transition table of condition lists, conditions cached per frame) suits content-heavy NPC behaviour tuned by non-programmers. Our default stays the framework `StateMachine<TEnum>`; adopt the SO form only when designers must author many behaviours.
