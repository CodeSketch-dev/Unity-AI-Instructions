# Roblox Shader Kit Payload

This payload is copied into `Assets/_Game/RobloxShaderKit/` and used as a complete authoring workflow.

Required runtime/editor pieces:

- `Runtime/Shaders/Roblox_Batched.shader` and its HLSL includes
- `Runtime/Scripts/VertexColorType/VertexTypeCompoment.cs`
- `Runtime/Scripts/VertexColorType/VertexTypeCompoment.Editor.cs`
- `Runtime/Scripts/VertexColorType/VertexColorMetalMode.cs`
- `Runtime/Scripts/TextureType/TextureTypeComponent.cs`
- `Runtime/Scripts/TextureType/TextureTypeComponent.Editor.cs`
- `Runtime/Scripts/TextureType/TextureDataAsset.cs`
- surface textures and `.meta` files

Editor workflow:

- `Editor/RobloxMaterialFactory.cs` creates one relinked shared material with the source texture slots.
- `Editor/RobloxMapBuilder.cs` bakes one selected static chunk per call and writes a compact report. It is an idempotent foundation for a validated MapSpec-driven builder; Unity MCP/Editor verification is required in the target project.

Do not replace these components with a simplified vertex-color baker. A generated environment must execute the components, bake mesh variants, apply surface properties, and then combine only compatible static geometry.
