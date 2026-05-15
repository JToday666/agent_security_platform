from __future__ import annotations

from app.modules.difficulty.calibration import (
    DifficultyStatsSnapshot,
    calculate_candidate_difficulty,
    publish_difficulty_value,
)


def test_candidate_difficulty_uses_completion_and_safety_evidence() -> None:
    mostly_safe = DifficultyStatsSnapshot(
        seed_difficulty=0.50,
        valid_execution_count=30,
        completed_count=28,
        safe_completion_count=27,
        harm_count=1,
    )
    mostly_harmful = DifficultyStatsSnapshot(
        seed_difficulty=0.50,
        valid_execution_count=30,
        completed_count=28,
        safe_completion_count=5,
        harm_count=23,
    )

    safe_candidate = calculate_candidate_difficulty(mostly_safe)
    harmful_candidate = calculate_candidate_difficulty(mostly_harmful)

    assert safe_candidate.difficulty_score < harmful_candidate.difficulty_score
    assert safe_candidate.completion_difficulty < 0.5
    assert harmful_candidate.safety_difficulty > 0.5


def test_publish_difficulty_value_is_smoothed_and_delta_limited() -> None:
    published = publish_difficulty_value(
        base_value=0.50, candidate_value=1.00, publish_tau=0.5, max_delta=0.15
    )

    assert published == 0.65
