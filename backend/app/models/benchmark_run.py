from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class TestRun(Base):
    """
    测评任务表 (Test Run Model)

    记录用户发起的一次完整的Agent安全测评任务概要信息。
    包括任务的基本信息、被测Agent详情、整体运行状态进度、成功失败统计以及各项时间指标。
    """
    __tablename__ = "test_runs"
    __table_args__ = (
        UniqueConstraint("user_id", "request_id"),
        Index("ix_test_runs_status_updated_at", "status", "updated_at"),
        Index("ix_test_runs_status_pause_deadline_at", "status", "pause_deadline_at"),
        Index(
            "ix_test_runs_worker_claim_lookup",
            "status",
            "claimed_by",
            "claim_heartbeat_at",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="任务主键ID")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="发起该测评任务的用户ID"
    )
    public_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False, comment="对外公开的唯一任务标识编号(用于分享和展示)")
    agent_name: Mapped[str] = mapped_column(Text, nullable=False, comment="被测Agent的名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务描述/备注信息")
    submit_method: Mapped[str] = mapped_column(Text, nullable=False, comment="任务提交方式(如：api、web)")
    public_to_leaderboard: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), comment="是否允许该成绩公开到排行榜中"
    )
    request_id: Mapped[str] = mapped_column(Text, nullable=False, comment="前端或API调用的幂等请求ID，防止重复调度执行")
    agent_base_url: Mapped[str] = mapped_column(Text, nullable=False, comment="被测Agent的接口调用基础地址")
    credential_ref: Mapped[str | None] = mapped_column(Text, nullable=True, comment="被测Agent认证凭证所在外部引用的标识关联")
    status: Mapped[str] = mapped_column(Text, nullable=False, index=True, comment="任务当前的整体状态(如：pending, executing, finished_success, finished_error)")
    sample_query_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, comment="提交任务时用于圈定测评样本的具体过滤条件快照")
    execution_config: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, comment="任务调度执行时的配置项(如最大提问次数、并发数限制等)")
    total_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="当前任务包含的测试样本总数"
    )
    completed_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="已完成(无论成功失败)的样本数量汇总"
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="调度并执行成功的测试样本数(系统级成功，不代表攻击成功或防御成功)"
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="调度或执行产生异常、奔溃等报错的样本数量"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="任务创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="任务最后更新时间"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="工作流引擎真正提配、调度该任务开始执行的实际时间"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="所有样本处理结束且报告生成后，记录该任务彻底完毕的时刻"
    )
    finalization_reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务终止或异常结单的最终原因/备注")
    pause_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="是否已经使用过一次暂停机会"
    )
    pause_deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="任务暂停后允许恢复的截止时间"
    )
    requested_action: Mapped[str | None] = mapped_column(Text, nullable=True, comment="当前待执行的控制动作")
    requested_action_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="记录最近一次用户控制动作请求时间"
    )
    claimed_by: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        index=True,
        comment="当前领取该任务的 worker 标识"
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="worker 首次领取该任务的时间"
    )
    claim_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="worker 最近一次心跳时间"
    )


class RunDataset(Base):
    """
    任务级数据集快照表 (Run Dataset Snapshot Model)

    将一次评测任务中用户选中的公开数据集集合固化为稳定快照，便于列表、详情和控制接口直接按数据集维度查询进度。
    """
    __tablename__ = "run_datasets"
    __table_args__ = (
        UniqueConstraint("run_id", "dataset_code"),
        Index("ix_run_datasets_run_id_status", "run_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="任务数据集快照主键ID")
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
        comment="关联的测评任务ID"
    )
    dataset_code: Mapped[str] = mapped_column(Text, nullable=False, index=True, comment="公开数据集ID，对应 risk_subtypes.code")
    dataset_name: Mapped[str] = mapped_column(Text, nullable=False, comment="公开数据集名称")
    order_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="数据集在本次任务中的执行顺序")
    status: Mapped[str] = mapped_column(Text, nullable=False, index=True, comment="数据集级生命周期状态")
    total_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="该数据集在本次任务中命中的样本总数"
    )
    completed_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="该数据集在本次任务中已完成的样本数"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="快照创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="快照最近更新时间"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="该数据集开始执行的时间"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="该数据集完成执行的时间"
    )


class RunSample(Base):
    """
    运行样本映射表 (Run Sample Connector Model)

    关联测评任务(TestRun)与基准测试集单体样本(BenchmarkSample)。
    由于每次任务可能仅选用部分类型/难度样本，因此需要有专门关系表。
    """
    __tablename__ = "run_samples"
    __table_args__ = (
        UniqueConstraint("run_id", "sample_id_ref"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="记录主键ID")
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
        comment="关联的测评任务ID"
    )
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        nullable=False,
        index=True,
        comment="关联的基准测试样本的主键ID"
    )
    order_no: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="如果在该任务中指定了样本编排执行顺序，记录其序号")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="加入任务队列的时间"
    )


class SampleExecution(Base):
    """
    单样本执行记录表 (Sample Execution Model)

    针对某一单体样本在具体任务下的某一次执行记录。
    支持重试（如：网络抖动引起失败后再次执行），并绑定至特定运行环境。
    """
    __tablename__ = "sample_executions"
    __table_args__ = (
        UniqueConstraint("run_sample_id", "retry_no"),
        Index("ix_sample_executions_run_id_status", "run_id", "status"),
        Index(
            "ix_sample_executions_run_sample_id_retry_no",
            "run_sample_id",
            "retry_no",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="执行记录主键ID")
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
        comment="所属任务ID(冗余字段以便于大批量聚合查询)"
    )
    run_sample_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("run_samples.id"),
        nullable=False,
        index=True,
        comment="映射关系ID(关联了具体的执行计划)"
    )
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        nullable=False,
        index=True,
        comment="对应的官方测试样本库的实体ID"
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, index=True, comment="执行的生命周期状态(pending, dispatching, executing, verifying, done, error等)")
    retry_no: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="当前记录属于第几次重试(首次默认0)")
    work_dir: Mapped[str | None] = mapped_column(Text, nullable=True, comment="分配到沙箱机进行执行的物理工作目录")
    entry_url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="向Agent真实投递该用例的请求URL/抓包URL线索")
    environment_ref: Mapped[str | None] = mapped_column(Text, nullable=True, comment="分配执行所关联的隔离容器或沙箱环境标识")
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始投递诱导指令的时刻"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成判定及扫尾清理的时刻"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="如果系统自身级别抛出崩溃或异常超时，记录具体Traceback或摘要")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="生成执行计划的时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="节点最后上报心跳或更新状态的时间"
    )


class ExecutionArtifact(Base):
    """
    交互与判定副产物表 (Execution Artifact Model)

    当运行过程发生时，保存产生的一些实体文件(如：注入脚本、被测Agent异常截图、网络抓包PCAP等)存储记录。
    便于作为后续追溯评判依据。
    """
    __tablename__ = "execution_artifacts"
    __table_args__ = (
        Index(
            "ix_execution_artifacts_sample_execution_id_artifact_type",
            "sample_execution_id",
            "artifact_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="副产物记录主键ID")
    sample_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_executions.id"),
        nullable=False,
        index=True,
        comment="其归属的具体运行实体ID"
    )
    artifact_type: Mapped[str] = mapped_column(Text, nullable=False, comment="产物类型(如：screenshot, log, payload)")
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False, comment="产物实体文件所存储的具体物理或对象存储URI")
    artifact_metadata: Mapped[dict[str, object] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        comment="附带的元信息(比如长宽、抓包包类描述等)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="记录落盘上传完毕保存时间"
    )


class OracleResult(Base):
    """
    单项判定结果表 (Oracle Result Model)

    针对每条样本对应的规则评判器(Oracle)，保存独立且原子的评估结果得分。
    """
    __tablename__ = "oracle_results"
    __table_args__ = (
        UniqueConstraint("sample_execution_id", "oracle_id"),
        CheckConstraint("score >= 0 AND score <= 1", name="score_range"),
        Index(
            "ix_oracle_results_sample_execution_id_matched",
            "sample_execution_id",
            "matched",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="判定明细ID")
    sample_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_executions.id"),
        nullable=False,
        index=True,
        comment="其归属的当条样本执行上下文的主键"
    )
    oracle_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_oracles.id"),
        nullable=False,
        index=True,
        comment="对应所调用的具体预言机/规则探测器标识"
    )
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="是否命中规则所描述的状态 (如攻击是否成功)")
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True, comment="该评估器判定打出的0-1之间的小数分数")
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="若判定由于某种输出而命中，则摘录该段输出/总结")
    evidence_ref: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True, comment="关联引用具体的判定依据线索，用于进一步排查")
    evaluator_version: Mapped[str | None] = mapped_column(Text, nullable=True, comment="判定当下所使用的预言机引擎版本，便于追溯算法一致性")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="结果落盘时间"
    )


class ExecutionSummary(Base):
    """
    执行聚合总结表 (Execution Summary Model)

    多项 Oracle 跑完之后，进行逻辑整合和加权分析，得出该条样本通过该次调度的【最终安全决断结果/标签】。
    """
    __tablename__ = "execution_summaries"
    __table_args__ = (
        UniqueConstraint("sample_execution_id"),
        Index(
            "ix_execution_summaries_task_completed_harm_detected",
            "task_completed",
            "harm_detected",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="汇总评价ID")
    sample_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_executions.id"),
        nullable=False,
        index=True,
        comment="单次样本调度上下文映射键"
    )
    task_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="Agent层面是否完成了用户本来的良性任务指派目标")
    harm_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="测评平台是否探测了预期破坏/被诱攻击成功的指标发生")
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="面向人类视角的该条测试行为全景综述总结评定")
    final_label: Mapped[str | None] = mapped_column(Text, nullable=True, comment="打上的内部结果分类词(如：safe, hijacked, timeout, refused)")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="生成总结报告时间"
    )


class SampleDifficultyStat(Base):
    """
    样本难易度统计表 (Sample Difficulty Stats)

    以数据仓库/数仓汇总理念建立的统计缓存表。
    用来不断修正、刻画各个样本(攻击手段)的历史有效利用率与天然被防范成功率。
    """
    __tablename__ = "sample_difficulty_stats"
    __table_args__ = (
        CheckConstraint(
            "valid_execution_count >= 0",
            name="valid_execution_count_nonnegative",
        ),
        CheckConstraint("harm_count >= 0", name="harm_count_nonnegative"),
        CheckConstraint(
            "safe_completion_count >= 0",
            name="safe_completion_count_nonnegative",
        ),
        CheckConstraint("harm_rate >= 0 AND harm_rate <= 1", name="harm_rate_range"),
        CheckConstraint(
            "safe_completion_rate >= 0 AND safe_completion_rate <= 1",
            name="safe_completion_rate_range",
        ),
        CheckConstraint(
            "inferred_difficulty >= 0 AND inferred_difficulty <= 1",
            name="inferred_difficulty_range",
        ),
    )

    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        primary_key=True,
        comment="官方样本基准ID"
    )
    valid_execution_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="历史所有跑过该用例的累计有效运行次数记录"
    )
    harm_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="历史以来成功使得被测端发生安全侵入/利用成功的次数累计"
    )
    safe_completion_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="防御生效且依然完成了良性目标的次数记录"
    )
    harm_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, comment="根据上述指标计算出来的安全损害检出历史比率(反应其杀伤力)")
    safe_completion_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, comment="成功防御的安全通过率")
    inferred_difficulty: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, comment="统计算法归一化后的相对防御难度指标量化分级")
    algorithm_version: Mapped[str] = mapped_column(Text, nullable=False, comment="计算当前统计维度所使用的衰减与算阶算法版本约定")
    last_execution_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="该用例最近一次被触发使用的时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        comment="统计数值最后刷新时间"
    )


class RunReport(Base):
    """
    任务最终测试报告书表 (Run Report)

    整体全部成功执行下发后，经由评估引擎收尾构建的呈现给用户的离线格式安全报告/成绩。
    """
    __tablename__ = "run_reports"
    __table_args__ = (
        UniqueConstraint("run_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="报告主键标识")
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
        comment="映射具体的测试调起任务实体"
    )
    report_status: Mapped[str] = mapped_column(Text, nullable=False, index=True, comment="当前组装报告状态(如：generating, available, failed)")
    summary_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True, comment="雷达图信息：分类安全得分汇总大json及结构化建议摘要")
    report_uri: Mapped[str | None] = mapped_column(Text, nullable=True, comment="生成的诸如PDF版本/归档富文本格式静态存储路径")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="排队或创建开始生成的记录时间"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="报告定稿完毕生成的最新归档时间"
    )
