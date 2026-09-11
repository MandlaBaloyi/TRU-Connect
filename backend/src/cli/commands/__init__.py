"""
One module per command family, each exposing a single AppGroup that
src/cli/__init__.py registers.

WHY FAMILIES AND NOT ONE FILE. `flask admin ...` and
`flask catalogue ...` answer different questions and will grow at
different rates -- verification is a third that does not exist yet.
Splitting them now costs nothing and means a new family is a new file
rather than an edit to a shared one.
"""
