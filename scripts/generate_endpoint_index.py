"""Scan FastAPI route decorators and emit markdown endpoint index rows."""
from __future__ import annotations

import re
from pathlib import Path

API = Path(__file__).resolve().parents[1] / "Backend" / "app" / "api"
OUT = Path(__file__).resolve().parents[1] / "docs" / "api" / "ENDPOINT_INDEX.md"

ROUTE_RE = re.compile(
    r"""@(?:\w+\.)?(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]""",
    re.IGNORECASE,
)
PREFIX_RE = re.compile(
    r"""(\w+)\s*=\s*APIRouter\([^)]*?prefix\s*=\s*['\"]([^'\"]*)['\"]""",
    re.IGNORECASE | re.DOTALL,
)
ROUTER_ASSIGN_RE = re.compile(r"""(\w+)\s*=\s*APIRouter\(\s*\)""")


def main() -> None:
    rows: list[tuple[str, str, str, str]] = []
    for path in sorted(API.rglob("*.py")):
        if path.name.startswith("_") or path.name == "dependencies.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        prefixes: dict[str, str] = {}
        for name, pref in PREFIX_RE.findall(text):
            prefixes[name] = pref
        for name in ROUTER_ASSIGN_RE.findall(text):
            prefixes.setdefault(name, "")

        # Associate each decorator with nearest preceding router name heuristically
        lines = text.splitlines()
        current_router = "router"
        for i, line in enumerate(lines):
            massign = re.match(r"^(\w+)\s*=\s*APIRouter", line)
            if massign:
                current_router = massign.group(1)
            m = re.search(
                r"""@(\w+)\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]""",
                line,
                re.I,
            )
            if not m:
                # multiline @router.get(
                m2 = re.search(r"""@(\w+)\.(get|post|put|patch|delete)\(\s*$""", line, re.I)
                if m2 and i + 1 < len(lines):
                    nxt = lines[i + 1]
                    mpath = re.search(r"""['\"]([^'\"]*)['\"]""", nxt)
                    if mpath:
                        rname, method, route = m2.group(1), m2.group(2).upper(), mpath.group(1)
                        pref = prefixes.get(rname, prefixes.get(current_router, ""))
                        full = f"{pref}{route}" if route.startswith("/") or route == "" else f"{pref}/{route}"
                        if route == "":
                            full = pref or "/"
                        rows.append((path.name, method, full or "/", "see module docs"))
                continue
            rname, method, route = m.group(1), m.group(2).upper(), m.group(3)
            pref = prefixes.get(rname, "")
            if route == "":
                full = pref or "/"
            elif pref:
                full = f"{pref}{route}" if route.startswith("/") else f"{pref}/{route}"
            else:
                full = route if route.startswith("/") else f"/{route}"
            rows.append((path.name, method, full, "see module docs"))

    # de-dupe
    seen = set()
    uniq = []
    for r in rows:
        key = (r[1], r[2])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    lines = [
        "# Full Endpoint Index",
        "",
        "Canonical prefix: **`/api/v1`**. Legacy unversioned mounts also exist.",
        "",
        "Interactive schemas: `GET /docs` (Swagger UI).",
        "",
        "| Method | Path | Source | Notes |",
        "|--------|------|--------|-------|",
    ]
    for src, method, path, notes in sorted(uniq, key=lambda x: (x[2], x[1])):
        lines.append(f"| `{method}` | `/api/v1{path}` | `{src}` | {notes} |")

    lines += [
        "",
        f"_Generated from route decorators · {len(uniq)} unique method/path pairs._",
        "",
        "## Documentation template",
        "",
        "For each endpoint in module guides:",
        "",
        "| Field | Content |",
        "|-------|---------|",
        "| Method / URL | Verb + path |",
        "| Description | Purpose |",
        "| Authentication | Public / JWT / Roles / Super |",
        "| Request | JSON or query schema |",
        "| Response | Success payload |",
        "| Status codes | Expected HTTP codes |",
        "| Example | curl |",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} with {len(uniq)} endpoints")


if __name__ == "__main__":
    main()
