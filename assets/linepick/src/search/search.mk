/// A one-based line number and a view of that line in the input.
export struct Hit {
    export number: int
    export line: str
}

/// Collect matching lines in input order. An empty pattern matches every line.
export Find(a: &Arena, input: str into a, pattern: str): OutOfMemory!List[Hit] from a, input {
    var hits := List[Hit].New(a)
    var number := 0
    for line in input.Lines() {
        number += 1
        if line.Has(pattern) {
            try hits.Push(Hit(number: number, line: line))
        }
    }
    return hits
}

test "preserves positions, UTF-8, and the unterminated last line" (sys: &System) {
    hits := try Find(sys.arena, "uno\r\ncafé noir\r\n\ncafé", "fé")
    Assert(hits.Len() == 2)
    Assert(hits[0].number == 2 && hits[0].line == "café noir")
    Assert(hits[1].number == 4 && hits[1].line == "café")
}

test "an empty pattern includes blank lines" (sys: &System) {
    hits := try Find(sys.arena, "\none\n", "")
    Assert(hits.Len() == 2)
    Assert(hits[0].line == "" && hits[1].line == "one")
}

test "empty input and a missing pattern yield no hits" (sys: &System) {
    empty := try Find(sys.arena, "", "")
    absent := try Find(sys.arena, "blue", "red")
    Assert(empty.Len() == 0 && absent.Len() == 0)
}
