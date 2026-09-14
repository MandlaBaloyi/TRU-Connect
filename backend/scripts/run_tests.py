"""
Run the backend test suite.

WHY THIS EXISTS AT ALL. Bare `pytest` does not work in this project and
never has. TestingConfig falls back to postgres:postgres, the real
credentials live in .env, and the password contains an "@" -- which reads
as the host separator if it is dropped into a DSN unencoded, producing a
connection error that looks like a broken database rather than a quoting
bug. SECRET_KEY and JWT_SECRET_KEY also have to be present or the app
factory refuses to build. So there were 1,197 tests and no supported way
to run them; this is the supported way.

ONE PYTEST PROCESS AT A TIME, ENFORCED RATHER THAN DOCUMENTED.
conftest.py drops and recreates schemas per test, so two concurrent runs
stomp each other's database. The symptom is a flood of
`relation "auth.users" does not exist` setup errors that look like a
broken migration and are not -- and the cost is worse than lost time,
because you cannot trust the result of EITHER run. That rule was written
down in CLAUDE.md and broken three times anyway, so it is a lock now.

With no target it walks the suite directory by directory, one process at
a time, and prints a summary at the end. That satisfies the same rule by
construction: sequential, never parallel.

    python scripts/run_tests.py                      # everything, in order
    python scripts/run_tests.py tests/domains/auth   # one directory
    python scripts/run_tests.py tests/domains/network/orders -k checkout

Run it from backend/ with the venv active.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

BACKEND = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND / ".env"
TESTS = BACKEND / "tests"
LOCK = BACKEND / ".pytest-running.lock"

#: pytest flags whose VALUE is the next argument rather than attached
#: with "=". Anything not listed is assumed to stand alone, which is the
#: safe default: a flag wrongly listed here would swallow a real test
#: path, while one wrongly omitted only reproduces the old behaviour for
#: that single flag.
VALUE_TAKING_FLAGS = {
    "-k", "-m", "-n", "-p", "-c", "-o", "--maxfail", "--deselect",
    "--ignore", "--timeout", "--durations", "--rootdir", "--junitxml",
}

#: The database tests are allowed to destroy. Deliberately NOT read from
#: .env: POSTGRES_DB is the development database, and a typo that pointed
#: the suite at it would drop every schema in it without asking.
TEST_DB = "tru_connect_test"


def read_env(path: Path) -> dict[str, str]:
    """Minimal .env parser -- no dependency, no surprises.

    Deliberately does not expand ${VARS} or handle multi-line values:
    this file only needs the flat KEY=VALUE pairs, and a parser that
    quietly half-supports a syntax is worse than one that does not.
    """
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def build_test_dsn(env: dict[str, str]) -> str:
    """The URL-encoding here is the whole point -- see the module docstring."""
    user = quote(env.get("POSTGRES_USER", "postgres"), safe="")
    password = quote(env.get("POSTGRES_PASSWORD", ""), safe="")
    host = env.get("POSTGRES_HOST", "localhost")
    port = env.get("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{TEST_DB}"


def redact(dsn: str) -> str:
    """Never print a DSN raw. A password was leaked into a transcript once
    by a filter that only masked values it thought looked secret."""
    if "://" not in dsn or "@" not in dsn:
        return dsn
    scheme, _, rest = dsn.partition("://")
    _, _, location = rest.rpartition("@")
    return f"{scheme}://***:***@{location}"


def process_alive(pid: int) -> bool:
    """os.kill(pid, 0) is not usable here -- on Windows it TERMINATES the
    process rather than probing it."""
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            return str(pid) in out
        out = subprocess.run(
            ["ps", "-p", str(pid)], capture_output=True, text=True, timeout=10
        ).stdout
        return str(pid) in out
    except Exception:
        # Cannot tell -- assume alive. Refusing to run is recoverable with
        # --force; a corrupted run silently is not.
        return True


def acquire_lock(force: bool) -> bool:
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text(encoding="utf-8").split()[0])
        except Exception:
            pid = -1
        if pid > 0 and process_alive(pid) and not force:
            print(f"\nREFUSING TO START: a test run (pid {pid}) is already going.")
            print("Two pytest processes drop each other's schemas and both")
            print("results become meaningless. Wait for it, or if you are")
            print("certain it is dead, re-run with --force.\n")
            return False
        LOCK.unlink(missing_ok=True)
    LOCK.write_text(f"{os.getpid()} {time.time()}", encoding="utf-8")
    return True


def discover_targets() -> list[Path]:
    """Every leaf worth its own process, in a stable order."""
    targets: list[Path] = []
    architecture = TESTS / "architecture"
    if architecture.is_dir():
        targets.append(architecture)
    domains = TESTS / "domains"
    if domains.is_dir():
        # SKIP __pycache__ AND ANYTHING ELSE DUNDER. Without this the
        # walk hands pytest tests/domains/__pycache__, which collects
        # nothing, exits non-zero, and shows up in the summary as a
        # FAILED suite -- a red line with no failing test behind it,
        # which is worse than useless because it trains you to ignore
        # the summary.
        targets.extend(
            sorted(
                p for p in domains.iterdir()
                if p.is_dir() and not p.name.startswith("__")
            )
        )
    shared = TESTS / "shared"
    if shared.is_dir():
        targets.append(shared)
    targets.extend(sorted(TESTS.glob("test_*.py")))
    return targets


def run(target: str, extra: list[str], env: dict[str, str]) -> int:
    print(f"\n{'=' * 70}\n  {target}\n{'=' * 70}", flush=True)
    return subprocess.run(
        [sys.executable, "-m", "pytest", target, *extra],
        cwd=BACKEND, env=env,
    ).returncode


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]

    dotenv = read_env(ENV_FILE)
    if not dotenv:
        print(f"No .env found at {ENV_FILE} -- cannot build test credentials.")
        return 2

    dsn = build_test_dsn(dotenv)
    env = os.environ.copy()
    env.update({
        "TEST_DATABASE_URL": dsn,
        "FLASK_ENV": "testing",
        "SECRET_KEY": dotenv.get("SECRET_KEY", "test-secret-key"),
        "JWT_SECRET_KEY": dotenv.get("JWT_SECRET_KEY", "test-jwt-secret-key"),
        # The suite must never send real email or touch a real queue.
        "MAIL_PROVIDER": "fake",
        "MAIL_ASYNC": "False",
        "AI_PROVIDER": "fake",
        "AI_DRY_RUN": "True",
    })

    print(f"database : {redact(dsn)}")
    print(f"python   : {sys.executable}")

    if not acquire_lock(force):
        return 1

    try:
        # SPLIT FLAGS FROM TARGETS BY SHAPE, not by position. The first
        # version took args[0] as the target, so `run_tests.py -q` ran
        # `pytest -q` -- the whole suite in ONE process, which is the exact
        # thing the directory walk exists to avoid, while reporting a
        # cheerful "1/1 green" for a target named "-q".
        #
        # AND A FLAG'S VALUE TRAVELS WITH IT. Shape alone split
        # `-k nearest_first` into a flag and a "target", so pytest got a
        # bare -k and died on "expected one argument" while the real test
        # file was never run. Only `-k=nearest_first` worked, which is a
        # thing nobody would guess.
        flags, named = [], []
        expecting_value = False
        for arg in args:
            if expecting_value:
                flags.append(arg)
                expecting_value = False
            elif arg.startswith("-"):
                flags.append(arg)
                expecting_value = arg in VALUE_TAKING_FLAGS
            else:
                named.append(arg)
        targets = named or [str(p.relative_to(BACKEND).as_posix()) for p in discover_targets()]
        extra = flags

        results: list[tuple[str, int]] = []
        for target in targets:
            results.append((target, run(target, extra, env)))

        print(f"\n{'=' * 70}\n  SUMMARY\n{'=' * 70}")
        for target, code in results:
            print(f"  {'PASS' if code == 0 else 'FAIL':<5} {target}")
        failed = [t for t, c in results if c != 0]
        print(f"\n{len(results) - len(failed)}/{len(results)} green")
        return 1 if failed else 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
