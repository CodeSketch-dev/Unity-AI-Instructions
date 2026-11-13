---
name: native-array-using-mutation
description: "Use when CS1654 or CS1612 occurs while mutating a NativeArray using variable or a struct-valued property, or the matching lint rule fires."
triggers: CS1654, CS1612, NativeArray using, readonly using variable, sua mang using, bien using chi doc
---

# Mutable NativeArray lifetime

A NativeArray is a value type. A variable declared by `using` is readonly; indexed writes can fail with CS1654 even when disposal is correct.

1. Read the declaration and the reported indexed write; keep read-only `using` arrays unchanged.
2. For mutation, declare an ordinary mutable NativeArray local. Put its work in `try` and `Dispose()` in `finally`; complete jobs that use it before disposal.
3. Preserve existing allocation, ownership, scheduling and exception cleanup. Do not bypass the compiler with unsafe writes or copy an owning array just to silence the error.
4. Verify the relevant assembly compiles and the actual scheduled test passes; lint success alone is not compile/runtime evidence.

CS1612 on an indexed write through a NativeArray-valued property needs a mutable local view of that same storage, then the indexed write through the view. This borrowed view does not acquire disposal ownership; keep disposal with its existing owner. Do not replace the storage or dispose the alias. Run changed-file lint before an expensive Editor refresh.

## Lint boundary and exceptions

The lexical rule tracks explicit NativeArray types, `using var` direct construction and aliases of locally proven arrays. It ignores comments/strings, read access, ordinary mutable arrays and other types. Arbitrary factory-return type inference, deconstruction and preprocessor semantics require compiler review; use an explicit NativeArray type when needed. The rule applies to Editor/tests too. A suppression is only for an intentional compiler-negative fixture, with a reason.

Foundation: no; this is a targeted C# compiler pitfall, enforced by the lint-triggered skill rather than global gameplay instructions.
