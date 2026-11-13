using Unity.Collections;
class GoodUsingArray
{
    NativeArray<int> values;
    void ReadOnly()
    {
        using var values = new NativeArray<int>(4, Allocator.Temp);
        int value = values[0];
        this.values[0] = value;
        var text = "values[0] = 2; { }";
        var verbatim = @"values[0]++";
        // values[0] = 2;
        /* values[0] += 2; */
    }
    void DifferentMethod()
    {
        var values = new NativeArray<int>(4, Allocator.Temp);
        values[0] = 2;
        values.Dispose();
    }
    void DifferentScopes()
    {
        { using NativeArray<int> values = GetValues(); Read(values[0]); }
        { NativeArray<int> values = GetValues(); values[0] = 2; values.Dispose(); }
        using var list = new NativeList<int>(Allocator.Temp);
        list[0] = 1;
    }
}
