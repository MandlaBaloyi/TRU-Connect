from pathlib import Path

ROOT = Path.cwd()

EXCLUDED = {
    "node_modules",
    ".git",
    ".expo",
    ".vscode",
    "__pycache__",
    ".idea",
    "android/.gradle",
}

def should_skip(path: Path):
    return any(part in EXCLUDED for part in path.parts)

def generate_tree(directory: Path, prefix=""):
    """Generate tree lines (list of strings) instead of printing."""
    lines = []
    items = sorted(
        [item for item in directory.iterdir() if not should_skip(item)],
        key=lambda x: (x.is_file(), x.name.lower())
    )

    for index, item in enumerate(items):
        connector = "└── " if index == len(items) - 1 else "├── "
        lines.append(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if index == len(items) - 1 else "│   "
            lines.extend(generate_tree(item, prefix + extension))

    return lines

# Build the full tree as a list of strings
tree_lines = [ROOT.name]
tree_lines.extend(generate_tree(ROOT))

# Write to structure.txt
output_path = ROOT / "structure.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(tree_lines))

print(f"Project tree saved to {output_path}")