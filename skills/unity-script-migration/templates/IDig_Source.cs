namespace Game.DigEgg
{
    // Implemented by events raised by a scene facade so a handler can tell which instance raised it (tests run several facades at once).
    public interface IDig_Source
    {
        object Source { get; }
    }
}
