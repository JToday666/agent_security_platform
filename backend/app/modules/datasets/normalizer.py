"""将原始样本目录预标准化为标准 task.json bundle。"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from app.modules.datasets.importer import (
    IGNORED_JSON_FILENAMES,
    ImportValidationError,
    detect_metadata_format,
    normalize_sample_metadata_file,
    planned_sample_to_standard_task_payload,
)


@dataclass(slots=True)
class NormalizationResult:
    """记录一次标准化执行的统计结果。"""

    input_root: Path
    output_root: Path
    sample_count: int = 0
    written_task_count: int = 0
    symlinked_file_count: int = 0


@dataclass(slots=True)
class _MetadataCandidate:
    """描述样本目录中的单个元数据候选文件。"""

    path: Path
    fmt: str
    payload: dict[str, object]


@dataclass(slots=True)
class _SelectedMetadata:
    """描述样本目录最终选中的元数据文件及其重复副本。"""

    path: Path
    fmt: str
    duplicate_paths: tuple[Path, ...]


def normalize_sample_bundle(
    input_root: Path,
    output_root: Path,
    mode: str = "auto",
    dry_run: bool = False,
) -> NormalizationResult:
    """把原始样本目录转换为只含标准 task.json 的导入目录。"""
    source_root = input_root.resolve()
    target_root = output_root.resolve()
    if not source_root.exists():
        raise ImportValidationError(f"样本根目录不存在: {source_root}")
    if mode not in {"auto", "legacy", "standard"}:
        raise ImportValidationError(f"不支持的扫描模式: {mode}")
    if target_root == source_root or source_root in target_root.parents:
        raise ImportValidationError("输出目录不能位于输入目录内部")

    selected_by_dir = _discover_selected_metadata(source_root, mode)
    result = NormalizationResult(input_root=source_root, output_root=target_root, sample_count=len(selected_by_dir))

    if dry_run:
        return result

    _prepare_output_root(target_root)
    for sample_dir, selected in selected_by_dir:
        planned_sample = normalize_sample_metadata_file(selected.path, source_root, selected.fmt)
        normalized_sample_dir = target_root / sample_dir.relative_to(source_root)
        normalized_sample_dir.mkdir(parents=True, exist_ok=True)
        task_path = normalized_sample_dir / "task.json"
        task_path.write_text(
            json.dumps(planned_sample_to_standard_task_payload(planned_sample), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result.written_task_count += 1
        excluded_paths = {selected.path, *selected.duplicate_paths}
        result.symlinked_file_count += _symlink_sample_resources(sample_dir, normalized_sample_dir, excluded_paths)

    return result


def _discover_selected_metadata(sample_root: Path, mode: str) -> list[tuple[Path, _SelectedMetadata]]:
    """发现并挑选每个样本目录中唯一可用的元数据文件。"""
    candidates_by_dir: dict[Path, list[_MetadataCandidate]] = defaultdict(list)
    for path in sorted(sample_root.rglob("*.json")):
        if path.name in IGNORED_JSON_FILENAMES or "saved_logs" in path.parts:
            continue
        payload = _load_candidate_payload(path)
        fmt = detect_metadata_format(payload)
        if fmt is None:
            continue
        candidates_by_dir[path.parent].append(_MetadataCandidate(path=path, fmt=fmt, payload=payload))

    selected_by_dir: list[tuple[Path, _SelectedMetadata]] = []
    for sample_dir in sorted(candidates_by_dir):
        selected = _select_metadata_candidate(sample_dir, candidates_by_dir[sample_dir], mode)
        if selected is not None:
            selected_by_dir.append((sample_dir, selected))

    if not selected_by_dir:
        raise ImportValidationError(f"未在 {sample_root} 下发现可导入的样本元数据")
    return selected_by_dir


def _load_candidate_payload(path: Path) -> dict[str, object] | object:
    """读取候选 JSON。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImportValidationError(f"JSON 解析失败: {path}: {exc}") from exc


def _select_metadata_candidate(
    sample_dir: Path,
    candidates: list[_MetadataCandidate],
    mode: str,
) -> _SelectedMetadata | None:
    """在样本目录中挑选唯一元数据文件，允许同内容副本去重。"""
    if mode == "auto":
        standard = [item for item in candidates if item.fmt == "standard"]
        legacy = [item for item in candidates if item.fmt == "legacy"]
        if standard and legacy:
            raise ImportValidationError(f"{sample_dir}: 同目录同时存在 standard 与 legacy 元数据")
        target = standard if standard else legacy
        return _dedupe_candidates(sample_dir, target)

    filtered = [item for item in candidates if item.fmt == mode]
    return _dedupe_candidates(sample_dir, filtered)


def _dedupe_candidates(sample_dir: Path, candidates: list[_MetadataCandidate]) -> _SelectedMetadata | None:
    """对同目录候选做内容去重，并选出优先元数据文件。"""
    if not candidates:
        return None

    fingerprints = {json.dumps(item.payload, ensure_ascii=False, sort_keys=True) for item in candidates}
    if len(fingerprints) > 1:
        raise ImportValidationError(f"{sample_dir}: 同目录存在多个可导入元数据文件且内容不一致")

    selected = min(
        candidates,
        key=lambda item: (0 if item.path.name == "task.json" else 1, item.path.name),
    )
    duplicates = tuple(item.path for item in candidates if item.path != selected.path)
    return _SelectedMetadata(path=selected.path, fmt=selected.fmt, duplicate_paths=duplicates)


def _prepare_output_root(output_root: Path) -> None:
    """确保输出目录可安全写入。"""
    if output_root.exists():
        if not output_root.is_dir():
            raise ImportValidationError(f"输出目录不是文件夹: {output_root}")
        if any(output_root.iterdir()):
            raise ImportValidationError(f"输出目录必须为空: {output_root}")
        return
    output_root.mkdir(parents=True, exist_ok=False)


def _symlink_sample_resources(sample_dir: Path, normalized_sample_dir: Path, excluded_paths: set[Path]) -> int:
    """为样本资源创建软链接，不复制被识别为元数据的 JSON 文件。"""
    symlink_count = 0
    for source_path in sorted(sample_dir.rglob("*")):
        if source_path.is_dir() or source_path in excluded_paths:
            continue
        relative_path = source_path.relative_to(sample_dir)
        target_path = normalized_sample_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(source_path.resolve())
        symlink_count += 1
    return symlink_count
