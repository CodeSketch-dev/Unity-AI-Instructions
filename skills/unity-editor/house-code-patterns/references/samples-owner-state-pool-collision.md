# Samples: owner components, state machine, pool, collision (SketchEngine form)

## Owner + parts
```csharp
public class AI_Component : MonoCached            // base only when many parts resolve the owner
{
    [SerializeField, HideInInspector] AI _ai;
    public AI AI { get { if (_ai == null) _ai = GetComponentInChildren<AI>(); return _ai; } }
    protected virtual void OnValidate() { if (!Application.isPlaying && _ai == null) _ai = AI; }
}
public class Character_Fx : MonoCachedHub<Character_Renderer>   // Hub resolves child, then parent
{
    void Play() => Hub.TransformCached.position += Vector3.up;
}
```

## State machine owner (one transition path)
```csharp
StateMachine<AI_State> _machine;
AI_State State { get => _machine.CurrentState; set => _machine.CurrentState = value; }
void InitStateMachine()
{
    _machine = new StateMachine<AI_State>();
    _idle = new AI_State_Idle(this);
    _idle.OnComplete += OnIdleComplete;
    _machine.AddState(AI_State.Idle, _idle);
    _machine.AddState(AI_State.Stop);          // label-only state
    _machine.CurrentState = AI_State.Stop;     // explicit initial state
}
void Update() => _machine.Update();            // the machine has no self-update
```
State class: `public class AI_State_Idle : IStateMachine` with `Init/OnStart/OnUpdate/OnFixedUpdate/OnStop/OnDestroy`, owner passed in the constructor, completion through `event Action OnComplete`. Enum numbers grouped (1.., 10.., 101..).

## Pool
```csharp
var fx = PoolPrefabGlobal.Get(Factory_Effect.FxDeath);       // PoolPrefabItem
fx.TransformCached.position = Hub.TransformCached.position + Vector3.up * 0.5f;
// later: PoolPrefabGlobal.Release(Factory_Effect.FxDeath, fx.gameObject);
```
`PoolPrefabConfig` assets live in `Configs/Pool/`, are listed by a `Factory_Pool`, and initialized once by a persistent pool manager prefab (`PoolPrefabGlobal.Init(configs)`).

## Collision
```csharp
public interface ICharacterCollidable
{
    void OnTriggerEnterFunc(Character c);  void OnTriggerExitFunc(Character c);
    void OnCollisionEnterFunc(Character c); void OnCollisionExitFunc(Character c);
}
public class Character : OptCollisionSensorFast<ICharacterCollidable>
{
    protected override void OnTriggerEnterFunc(ICharacterCollidable t) => t.OnTriggerEnterFunc(this);
}
public class Checkpoint : OptCollisionRegister, ICharacterCollidable   // non-generic register
{
    public void OnTriggerEnterFunc(Character c) { /* tiny body */ }
    public void OnTriggerExitFunc(Character c) { }
    public void OnCollisionEnterFunc(Character c) { }
    public void OnCollisionExitFunc(Character c) { }
}
```
Overrides of `Awake/OnEnable/OnDisable/OnValidate` call `base`.
