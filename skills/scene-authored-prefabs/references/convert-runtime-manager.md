# Converting a runtime-created manager to a scene-authored prefab

1. Find the creation site (`new GameObject`, `AddComponent<T>`, `SafeInstance`, `Resources.Load` + `Instantiate`).
2. Build the object once in the Editor (MCP script or a menu tool): GameObject + component + serialized references, save as `Assets/_Game/Prefabs/<Feature>/<Name>.prefab` (`SaveAsPrefabAssetAndConnect` on the scene instance).
3. Place it as a child of the owner (`Manager` of the persistent root, or the scene master prefab).
4. Resolution order in code: serialized reference on the master -> `FindFirstObjectByType<T>()` scene lookup -> (Editor tests only) runtime creation behind `#if UNITY_EDITOR` or a test flag. Log a warning when the fallback is used.
5. Remove the production creation path once Play shows the scene instance serving requests (check the instance id in a log line).
6. Reopen the scene, count missing scripts, Play 5 s, empty Console.

```csharp
// Editor snippet: promote a scene object to a prefab instance
var go = GameObject.Find("MyManager");
const string path = "Assets/_Game/Prefabs/Feature/MyManager.prefab";
PrefabUtility.SaveAsPrefabAssetAndConnect(go, path, InteractionMode.AutomatedAction);
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(go.scene);
```
