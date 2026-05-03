"""提交模块与运行时共享的轻量校验规则。"""


def is_valid_request_id(value: str) -> bool:
    """校验外部传入的请求编号格式。"""
    if not (6 <= len(value) <= 128):
        return False
    if not value[0].isalnum():
        return False
    return all(char.isalnum() or char in {"_", "-"} for char in value)


def difficulty_bucket_bounds(difficulty: float) -> tuple[float, float, bool]:
    """返回难度值对应的样本筛选区间。"""
    lower = max(0.0, round(difficulty - 0.05, 2))
    upper = min(1.0, round(difficulty + 0.05, 2))
    include_upper = upper == 1.0
    return lower, upper, include_upper
