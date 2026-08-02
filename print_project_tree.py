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
    """Determine whether a file/folder should be skipped."""

    if any(part in EXCLUDED for part in path.parts):
        return True

    if path.name in EXCLUDED_FILES:
        return True

    if path.is_file() and path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    return False


def generate_tree(directory: Path, prefix=""):
    """Generate a directory tree as a list of strings."""

    lines = []

    items = sorted(
        [item for item in directory.iterdir() if not should_skip(item)],
        key=lambda x: (x.is_file(), x.name.lower()),
    )

    for index, item in enumerate(items):
        connector = "└── " if index == len(items) - 1 else "├── "
        lines.append(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if index == len(items) - 1 else "│   "
            lines.extend(generate_tree(item, prefix + extension))

    return lines


def save_tree(start_directory: Path, output_filename: str):
    """Generate and save one tree."""

    if not start_directory.exists():
        return

    tree = [start_directory.name]
    tree.extend(generate_tree(start_directory))

    output_path = ROOT / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tree))


def main():
    # Entire project
    save_tree(ROOT, "structure.txt")

    # Backend only
    save_tree(ROOT / "backend", "backend_structure.txt")

    # Frontend only
    save_tree(ROOT / "frontend", "frontend_structure.txt")


if __name__ == "__main__":
    main()