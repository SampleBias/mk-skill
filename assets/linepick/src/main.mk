import src.search
import std.fs

export Main(sys: &System): OutOfMemory|WriteError!int {
    if sys.args.Len() != 3 {
        try sys.PrintErr("usage: linepick PATTERN FILE\n")
        return 2
    }
    path := sys.args[2]
    input := fs.ReadText(sys.arena, sys.io, path) else e {
        try sys.PrintErr("{path}: {e}\n", (path, e))
        return 2
    }
    var arena := try Arena.New(sys.heap)
    defer arena.Free()
    hits := try search.Find(&arena, input, sys.args[1])
    for hit in hits {
        try sys.Print("{n}: {line}\n", (n: hit.number, line: hit.line))
    }
    return if hits.Len() == 0 { 1 } else { 0 }
}
