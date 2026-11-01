// Replace {{Namespace}} and {{Prefix}}. Rename the file to I<Prefix>_Source.cs.
namespace {{Namespace}}
{
    // Implemented by events raised by a scene facade so a handler can tell which instance raised it (tests run several facades at once).
    public interface I{{Prefix}}_Source
    {
        object Source { get; }
    }
}
