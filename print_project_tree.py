from pathlib import Path

ROOT = Path.cwd()

# Folders to ignore
EXCLUDED = {
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".git",
    ".expo",
    ".vscode",
    ".idea",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".coverage",
    "dist",
    "build",
    ".next",
    ".cache",
}

# File extensions to ignore
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".sqlite3",
    ".db",
}

# Individual files to ignore
EXCLUDED_FILES = {
    ".DS_Store",
    "Thumbs.db",
}


def should_skip(path: Path):
    # Skip excluded folders
    if any(part in EXCLUDED for part in path.parts):
        return True

    # Skip excluded files
    if path.name in EXCLUDED_FILES:
        return True

    # Skip excluded file types
    if path.is_file() and path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    return False


def generate_tree(directory: Path, prefix=""):
    """Generate project tree as a list of strings."""
    lines = []

    items = sorted(
        [
            item
            for item in directory.iterdir()
            if not should_skip(item)
        ],
        key=lambda x: (x.is_file(), x.name.lower()),
    )

    for index, item in enumerate(items):
        connector = "└── " if index == len(items) - 1 else "├── "
        lines.append(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if index == len(items) - 1 else "│   "
            lines.extend(generate_tree(item, prefix + extension))

    return lines


def main():
    tree_lines = [ROOT.name]
    tree_lines.extend(generate_tree(ROOT))

    output_path = ROOT / "structure.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    print(f" Project tree saved to {output_path}")


if __name__ == "__main__":
    main()