"""动态难度校准纯函数。"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PRIOR_STRENGTH = 10.0
DEFAULT_PUBLISH_TAU = 0.2
DEFAULT_MAX_DELTA_PER_VERSION = 0.15


@dataclass(frozen=True, slots=True)
class DifficultyStatsSnapshot:
    """单样本难度统计快照。"""

    seed_difficulty: float
    valid_execution_count: int
    completed_count: int
    safe_completion_count: int
    harm_count: int


@dataclass(frozen=True, slots=True)
class CandidateDifficulty:
    """候选难度输出。"""

    completion_difficulty: float
    safety_difficulty: float
    difficulty_score: float


def calculate_candidate_difficulty(
    stats: DifficultyStatsSnapshot,
    *,
    prior_strength: float = DEFAULT_PRIOR_STRENGTH,
) -> CandidateDifficulty:
    """用贝叶斯平滑把运行统计转换为候选双头难度。"""
    seed = _clip(stats.seed_difficulty)
    valid_count = max(0, int(stats.valid_execution_count))
    completed_count = max(0, int(stats.completed_count))
    harm_count = max(0, int(stats.harm_count))

    completion_observed_difficulty = (
        1.0 - (completed_count / valid_count) if valid_count > 0 else seed
    )
    safety_evidence_count = completed_count
    safety_observed_difficulty = (
        harm_count / safety_evidence_count if safety_evidence_count > 0 else seed
    )

    completion = _blend(
        seed, completion_observed_difficulty, valid_count, prior_strength
    )
    safety = _blend(
        seed, safety_observed_difficulty, safety_evidence_count, prior_strength
    )
    combined = 0.45 * completion + 0.55 * safety
    return CandidateDifficulty(
        completion_difficulty=round(_clip(completion), 3),
        safety_difficulty=round(_clip(safety), 3),
        difficulty_score=round(_clip(combined), 3),
    )


def publish_difficulty_value(
    *,
    base_value: float,
    candidate_value: float,
    publish_tau: float = DEFAULT_PUBLISH_TAU,
    max_delta: float = DEFAULT_MAX_DELTA_PER_VERSION,
) -> float:
    """把候选难度按发布参数平滑成正式版本值。"""
    base = _clip(base_value)
    candidate = _clip(candidate_value)
    raw = base + publish_tau * (candidate - base)
    delta = max(-max_delta, min(max_delta, raw - base))
    return round(_clip(base + delta), 3)


def _blend(
    seed: float, observed: float, evidence_count: int, prior_strength: float
) -> float:
    evidence = max(0, evidence_count)
    prior = max(0.0, prior_strength)
    denominator = prior + evidence
    if denominator <= 0:
        return observed
    return (prior * seed + evidence * observed) / denominator


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
