"""Runtime orchestration exceptions."""


class RuntimeExecutionError(RuntimeError):
    """Base error for worker-managed runtime execution."""


class RuntimePreparationError(RuntimeExecutionError):
    """Raised when the runtime workspace cannot be prepared."""


class RuntimeStartupError(RuntimeExecutionError):
    """Raised when the probe runner cannot be started."""


class RuntimeDispatchError(RuntimeExecutionError):
    """Raised when dispatching into the probe runner fails."""


class RuntimeDispatchTimeout(RuntimeExecutionError):
    """Raised when the runtime does not finalize before timeout."""
