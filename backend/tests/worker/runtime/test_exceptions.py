from __future__ import annotations

import pytest

from app.worker.runtime.exceptions import (
    RuntimeDispatchError,
    RuntimeDispatchTimeout,
    RuntimeExecutionError,
    RuntimePreparationError,
    RuntimeStartupError,
)

pytestmark = pytest.mark.worker


def test_runtime_exception_hierarchy_is_stable() -> None:
    assert issubclass(RuntimeExecutionError, RuntimeError)
    assert issubclass(RuntimePreparationError, RuntimeExecutionError)
    assert issubclass(RuntimeStartupError, RuntimeExecutionError)
    assert issubclass(RuntimeDispatchError, RuntimeExecutionError)
    assert issubclass(RuntimeDispatchTimeout, RuntimeExecutionError)


def test_runtime_exceptions_preserve_error_message() -> None:
    assert str(RuntimePreparationError("prepare failed")) == "prepare failed"
    assert str(RuntimeStartupError("startup failed")) == "startup failed"
    assert str(RuntimeDispatchError("dispatch failed")) == "dispatch failed"
    assert str(RuntimeDispatchTimeout("dispatch timed out")) == "dispatch timed out"
