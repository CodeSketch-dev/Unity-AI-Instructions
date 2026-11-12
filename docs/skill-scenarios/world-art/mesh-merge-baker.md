# Scenario: mesh-merge-baker

**Prompt:** Bake the finished stage into chunks with colliders and navmesh.

**Expected:** Chunk meshes <=65k verts, generated box colliders not MeshColliders, navmesh bake then save scene, render-stats with measured_on.

**Must not:** Add MeshColliders on merged visuals or skip saving the scene.
