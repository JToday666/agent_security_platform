from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.modules.datasets.db_support import sync_pk_sequence


def test_sync_pk_sequence_rejects_invalid_identifiers() -> None:
    session = Mock()

    with pytest.raises(ValueError):
        sync_pk_sequence(session, "benchmark-samples")
    with pytest.raises(ValueError):
        sync_pk_sequence(session, "benchmark_samples", "bad-column")

    session.execute.assert_not_called()


def test_sync_pk_sequence_executes_setval_statement() -> None:
    session = Mock()

    sync_pk_sequence(session, "benchmark_samples")

    session.execute.assert_called_once()
    statement = session.execute.call_args.args[0]
    sql_text = str(statement)
    assert "pg_get_serial_sequence('benchmark_samples', 'id')" in sql_text
    assert "SELECT MAX(id) FROM benchmark_samples" in sql_text
