"""Prune expired runtime storage under the platform data root."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts._common import settings


@dataclass(frozen=True)
class PruneConfig:
    data_root: Path
    tmp_days: int = 7
    runtime_days: int = 14
    log_days: int = 30
    artifact_days: int = 180
    include_artifacts: bool = False
    apply: bool = False


@dataclass(frozen=True)
class PruneCandidate:
    category: str
    path: Path
    size_bytes: int
    age_days: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _age_days(path: Path, now: datetime) -> int:
    return max(0, int((now - _mtime(path)).total_seconds() // 86400))


def _is_old(path: Path, *, days: int, now: datetime) -> bool:
    return _mtime(path) < now - timedelta(days=days)


def _resolve(path: Path) -> Path:
    return path.expanduser().resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_child(path: Path, root: Path) -> Path:
    resolved = _resolve(path)
    resolved_root = _resolve(root)
    if resolved == resolved_root or not _is_relative_to(resolved, resolved_root):
        raise ValueError(f"Refuse to prune outside allowed root: {resolved}")
    return resolved


def _safe_data_root(path: Path) -> Path:
    resolved = _resolve(path)
    project_roots = [BACKEND_ROOT.resolve()]
    repo_root = BACKEND_ROOT.parent.resolve()
    if repo_root != repo_root.parent:
        project_roots.append(repo_root)
    for project_root in project_roots:
        if _is_relative_to(resolved, project_root):
            raise ValueError(f"Data root must not be inside project checkout: {resolved}")
    return resolved


def _path_size(path: Path) -> int:
    if path.is_symlink():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_symlink() or not child.is_file():
            continue
        total += child.stat().st_size
    return total


def _iter_children(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return list(root.iterdir())


def _rotated_log_file(path: Path) -> bool:
    name = path.name
    return (
        ".log." in name
        or name.endswith((".gz", ".zip", ".old", ".bak"))
        or name.startswith(("access.log-", "error.log-"))
    )


def _candidate(
    category: str, path: Path, *, now: datetime, root: Path
) -> PruneCandidate:
    safe_path = _safe_child(path, root)
    return PruneCandidate(
        category=category,
        path=safe_path,
        size_bytes=_path_size(safe_path),
        age_days=_age_days(safe_path, now),
    )


def discover_candidates(config: PruneConfig, *, now: datetime | None = None) -> list[PruneCandidate]:
    current_time = now or _utc_now()
    data_root = _safe_data_root(config.data_root)
    candidates: list[PruneCandidate] = []

    tmp_root = data_root / "tmp"
    for path in _iter_children(tmp_root):
        if not path.is_symlink() and _is_old(path, days=config.tmp_days, now=current_time):
            candidates.append(_candidate("tmp", path, now=current_time, root=tmp_root))

    runtime_workdir_root = data_root / "runtime" / "workdir"
    for path in _iter_children(runtime_workdir_root):
        if not path.is_symlink() and _is_old(path, days=config.runtime_days, now=current_time):
            candidates.append(
                _candidate("runtime_workdir", path, now=current_time, root=runtime_workdir_root)
            )

    logs_root = data_root / "logs"
    if logs_root.exists():
        for path in logs_root.rglob("*"):
            if (
                path.is_file()
                and not path.is_symlink()
                and _rotated_log_file(path)
                and _is_old(path, days=config.log_days, now=current_time)
            ):
                candidates.append(_candidate("rotated_log", path, now=current_time, root=logs_root))

    if config.include_artifacts:
        artifacts_root = data_root / "artifacts" / "evaluations"
        for path in _iter_children(artifacts_root):
            if (
                not path.is_symlink()
                and _is_old(path, days=config.artifact_days, now=current_time)
            ):
                candidates.append(_candidate("artifact_evaluation", path, now=current_time, root=artifacts_root))

    return candidates


def apply_prune(candidates: list[PruneCandidate], *, dry_run: bool) -> dict[str, object]:
    deleted: list[str] = []
    errors: list[dict[str, str]] = []
    if not dry_run:
        for candidate in candidates:
            try:
                if candidate.path.is_dir():
                    shutil.rmtree(candidate.path)
                else:
                    candidate.path.unlink()
                deleted.append(str(candidate.path))
            except Exception as exc:  # pragma: no cover - filesystem guard
                errors.append({"path": str(candidate.path), "error": str(exc)})

    categories: dict[str, dict[str, int]] = {}
    for candidate in candidates:
        bucket = categories.setdefault(candidate.category, {"count": 0, "sizeBytes": 0})
        bucket["count"] += 1
        bucket["sizeBytes"] += candidate.size_bytes

    return {
        "dryRun": dry_run,
        "candidateCount": len(candidates),
        "candidateBytes": sum(candidate.size_bytes for candidate in candidates),
        "deletedCount": len(deleted),
        "deletedBytes": sum(
            candidate.size_bytes for candidate in candidates if str(candidate.path) in deleted
        ),
        "categories": categories,
        "errors": errors,
        "candidates": [
            {
                "category": candidate.category,
                "path": str(candidate.path),
                "sizeBytes": candidate.size_bytes,
                "ageDays": candidate.age_days,
            }
            for candidate in candidates
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prune expired ASP runtime/tmp/log/artifact files. Dry-run by default."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=settings.data_root,
        help="Platform data root. Defaults to ASP_DATA_ROOT or /data/agent-security-platform.",
    )
    parser.add_argument("--tmp-days", type=int, default=7)
    parser.add_argument("--runtime-days", type=int, default=14)
    parser.add_argument("--log-days", type=int, default=30)
    parser.add_argument("--artifact-days", type=int, default=180)
    parser.add_argument(
        "--include-artifacts",
        action="store_true",
        help="Also prune old artifacts/evaluations children. Off by default.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete candidates. Without this flag the command only prints a plan.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = PruneConfig(
        data_root=args.data_root,
        tmp_days=args.tmp_days,
        runtime_days=args.runtime_days,
        log_days=args.log_days,
        artifact_days=args.artifact_days,
        include_artifacts=args.include_artifacts,
        apply=args.apply,
    )
    candidates = discover_candidates(config)
    result = apply_prune(candidates, dry_run=not config.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
