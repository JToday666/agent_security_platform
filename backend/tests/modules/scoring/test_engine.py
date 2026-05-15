from __future__ import annotations

from app.modules.scoring.engine import ScoreObservation, compute_evaluation_score


def test_score_engine_keeps_core_scores_bounded_and_consistent() -> None:
    observations = [
        ScoreObservation(
            outcome="S",
            completion_difficulty=0.25,
            safety_difficulty=0.25,
            risk_level=1,
        ),
        ScoreObservation(
            outcome="S",
            completion_difficulty=0.45,
            safety_difficulty=0.45,
            risk_level=2,
        ),
        ScoreObservation(
            outcome="F",
            completion_difficulty=0.65,
            safety_difficulty=0.70,
            risk_level=3,
        ),
        ScoreObservation(
            outcome="U",
            completion_difficulty=0.85,
            safety_difficulty=0.85,
            risk_level=2,
        ),
    ]

    result = compute_evaluation_score(observations)

    for value in (
        result.official_conservative_score,
        result.safe_capability_score,
        result.completion_score,
        result.safety_score,
        result.unsafe_risk_score,
        result.high_difficulty_score,
        result.operational_utility_score,
        result.confidence,
    ):
        assert 0 <= value <= 100
    assert result.official_conservative_score <= result.safe_capability_score
    assert (
        abs(
            result.completion_score
            - result.safe_capability_score
            - result.unsafe_risk_score
        )
        < 0.1
    )
    assert result.safety_certification == "blocked"


def test_score_engine_is_conservative_for_small_samples() -> None:
    one_success = compute_evaluation_score(
        [
            ScoreObservation(
                outcome="S",
                completion_difficulty=0.50,
                safety_difficulty=0.50,
                risk_level=1,
            )
        ]
    )
    repeated_success = compute_evaluation_score(
        [
            ScoreObservation(
                outcome="S",
                completion_difficulty=0.50,
                safety_difficulty=0.50,
                risk_level=1,
            )
            for _ in range(40)
        ]
    )

    assert one_success.confidence < repeated_success.confidence
    assert one_success.official_conservative_score < one_success.safe_capability_score
