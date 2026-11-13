using Unity.Collections;
class BadUsingArray
{
    void A()
    {
        using var values = new NativeArray<int>(4, Allocator.Temp);
        values[0] = 1; // bad
        values[1] += 2; // bad
        ++values[2]; // bad
    }
    void B()
    {
        using Unity.Collections.NativeArray<int> values = GetValues();
        values[0]--; // bad
    }
    void C()
    {
        using (var values = new NativeArray<int>(4, Allocator.Temp))
        {
            values[0] = 2; // bad
        }
    }
}
