"""基准数据集相关 ORM 模型，描述样本、分类与展示元数据。"""

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

from app.platform.db.base import Base


class DatasetSource(Base):
    """
    数据集来源表 (Dataset Source Model)

    维护系统中支持拉取或同步的安全数据集来源（如内部自建库、外部学术集等）。
    """

    __tablename__ = "dataset_sources"

    id: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, comment="来源主键ID"
    )
    code: Mapped[str] = mapped_column(
        Text, unique=True, index=True, nullable=False, comment="来源唯一编码"
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="来源别名/展示名")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="详细描述"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="记录创建时间",
    )


class AttackDeliveryType(Base):
    """
    攻击注入手段类型表 (Attack Delivery Type Model)

    描述某一个恶意样本是如何投递进Agent上下文的(如: 隐写提示、越权越狱、间接注入等)。
    """

    __tablename__ = "attack_delivery_types"

    id: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, comment="注入手段主键ID"
    )
    code: Mapped[str] = mapped_column(
        Text, unique=True, index=True, nullable=False, comment="唯一特征编码"
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="注入手段展示名")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="该注入类型的技术详情或补充说明"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="记录创建时间",
    )


class RiskCategory(Base):
    """
    大类安全风险分类表 (Risk Category Model)

    对风险分类的一级维度抽象（例如：机密性泄露、完整性篡改、违规生成等大类别）。
    """

    __tablename__ = "risk_categories"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, comment="大类ID")
    code: Mapped[str] = mapped_column(
        Text, unique=True, index=True, nullable=False, comment="分类唯一代码"
    )
    name: Mapped[str] = mapped_column(
        Text, nullable=False, comment="分类规范名称(如：机密性泄露)"
    )
    meaning: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="该大类的安全意义及考核目的标准解读"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="更详细的描述信息"
    )
    translations: Mapped[dict[str, dict[str, object]]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="按 locale 存储的风险大类展示字段翻译",
    )
    sort_order: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
        comment="前端UI展示或大屏呈现时的排序字段",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否有效",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间",
    )


class RiskSubtype(Base):
    """
    具体的安全风险子类表 (Risk Subtype Model)

    具体到某种特定攻击向量（例如：身份越权、SQL注入）的二级维系，必须归属于一个父级大类。
    """

    __tablename__ = "risk_subtypes"
    __table_args__ = (UniqueConstraint("category_id", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="子类ID")
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("risk_categories.id"),
        nullable=False,
        index=True,
        comment="归属的一级风险大类ID",
    )
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment="子类唯一特征码(全局唯一的公开数据集ID)",
    )
    name: Mapped[str] = mapped_column(
        Text, nullable=False, comment="具体诱骗或攻击类别名"
    )
    translations: Mapped[dict[str, dict[str, object]]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="按 locale 存储的风险子类展示字段翻译",
    )
    sort_order: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="列表呈现时的排序支持"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否激活支持测算",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="记录生成时间",
    )


class RiskSubtypeDisplayMeta(Base):
    """
    风险子类在Web前端的富文本呈现/多媒体介绍映射记录表 (Risk Subtype Display Meta)

    当在前端知识库或者雷障词典展示某一个特定攻击子域时需要的详尽静态资料。
    """

    __tablename__ = "risk_subtype_display_meta"

    subtype_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("risk_subtypes.id"),
        primary_key=True,
        comment="映射的一对一关联风险子类主键",
    )
    short_description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="一句话精简业务概括描述"
    )
    full_description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="全面的长篇幅 Markdown 富文本知识讲解"
    )
    highlights: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="提炼核心特质或难点以列表记录(List<str>)",
    )
    scenarios: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="典型的受影响业务场景罗列(List<str>)",
    )
    resources: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="外部关联文件及文档引用(List<Dict>)",
    )
    media: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="包含在富文本中所需的图片或视频演示材料(List<Dict>)",
    )
    translations: Mapped[dict[str, dict[str, object]]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="按 locale 存储的展示元数据翻译",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="资料最后更新归档日",
    )


class AssetType(Base):
    """
    相关受保护资产标的类型表 (Asset Type Model)

    定义一条安全测试用例试图窃取或破坏的具体客观资产实体类型（如：私人图库、凭证密码、敏感账单等）。
    """

    __tablename__ = "asset_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="资产标的ID")
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        index=True,
        nullable=False,
        comment="类型编码规则(如：asset_credential)",
    )
    name: Mapped[str] = mapped_column(
        Text, nullable=False, comment="被保护资产官方学名"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="描述以及涉及的数据分级评定"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建的时间点",
    )


class BenchmarkSample(Base):
    """
    基准测评用例(核心样本)表 (Benchmark Sample Model)

    代表一条独立的、可复现的安全评估用例。
    包含此用例的来源、分类、物理文件路径追踪、困难度算阶结果以及期望它的防御表现目标。
    """

    __tablename__ = "benchmark_samples"
    __table_args__ = (
        UniqueConstraint("dataset_source_id", "sample_id"),
        CheckConstraint("risk_level IN (1, 2, 3)", name="risk_level_range"),
        CheckConstraint("attack_level IN (1, 2, 3)", name="attack_level_range"),
        CheckConstraint(
            "difficulty_seed >= 0 AND difficulty_seed <= 1",
            name="difficulty_seed_range",
        ),
        CheckConstraint(
            "difficulty_score >= 0 AND difficulty_score <= 1",
            name="difficulty_score_range",
        ),
        Index(
            "ix_benchmark_samples_risk_subtype_id_risk_level_attack_level",
            "risk_subtype_id",
            "risk_level",
            "attack_level",
        ),
        Index(
            "ix_benchmark_samples_dataset_source_id_is_active",
            "dataset_source_id",
            "is_active",
        ),
        Index(
            "ix_benchmark_samples_is_active_difficulty_score",
            "is_active",
            "difficulty_score",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="基准测试样本表本地主键"
    )
    dataset_source_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("dataset_sources.id"),
        nullable=False,
        index=True,
        comment="归属的数据集来源标志ID",
    )
    sample_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="该来源数据集下声明的原始唯一标号(不与其他来源冲突)",
    )
    sample_name: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="样本标题/自然语言称呼"
    )
    resource_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="存放其依赖运行的辅助沙箱文件/配置(如：隔离容器目录定义)位置",
    )
    entry_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="向被测Agent发起实际请求需要解析注入的最核心入口投递文件路径",
    )
    user_goal: Mapped[str] = mapped_column(
        Text, nullable=False, comment="用户的表面正常请求目标(用于掩护恶意攻击)"
    )
    attacker_goal: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="攻击者隐藏在该请求背后的真实破坏目的"
    )
    attacker_is_user: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="攻击者是否具有当前模拟用例受害者一第一人称控制权伪装身份",
    )
    attack_delivery_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("attack_delivery_types.id"),
        nullable=False,
        index=True,
        comment="注入方案及投寄技术类型关联",
    )
    risk_subtype_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("risk_subtypes.id"),
        nullable=False,
        index=True,
        comment="该样本试图利用的安全漏洞精确二级分类ID",
    )
    risk_level: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, index=True, comment="静态评估的主观危险级别(1-3)"
    )
    attack_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        index=True,
        comment="静态评估该手法的注入技术隐蔽度及难度分级(1-3)",
    )
    difficulty_seed: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        comment="入库时基准所携带的初始默认人工预估难度权重",
    )
    difficulty_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        index=True,
        comment="结合系统长线多次测评大盘通过率反向拟合生成的动态挑战难度系数(0-1)",
    )
    difficulty_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最近一次通过后台批处理作业重算动态更新难度得分的时间",
    )
    asset_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("asset_types.id"),
        nullable=True,
        index=True,
        comment="测试用例拟破坏的核心资料或者被利用的虚拟资源标的特征类型",
    )
    expected_safe_behavior: Mapped[str] = mapped_column(
        Text, nullable=False, comment="该场景下满分防御的预期理论应对行为要求描述"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True,
        comment="该基准样本是否仍然对外公开并纳入日常可用题库池",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="样本建档纳入时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="样本数据修因订立与排查修正发生的最后变动点",
    )


class SampleOracle(Base):
    """
    样本内置预言机(评判规则)表 (Sample Oracle Model)

    定义了校验一个样本在跑完环境后，如何通过某些工具提取特征或者关键字对比来推断它究竟算是“防守成功”还是被“攻击沦陷”。
    一条样本可能会配置多个探针综合算分。
    """

    __tablename__ = "sample_oracles"
    __table_args__ = (
        UniqueConstraint("sample_id_ref", "oracle_kind", "seq_no"),
        CheckConstraint("oracle_kind IN (1, 2)", name="oracle_kind_range"),
        Index(
            "ix_sample_oracles_sample_id_ref_oracle_kind",
            "sample_id_ref",
            "oracle_kind",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="探测规则记录ID"
    )
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        nullable=False,
        index=True,
        comment="它用来监督的对应的基准测试用例ID",
    )
    oracle_kind: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="测评机制体系(如 1-验证是否成功拒绝了攻击; 2-验证良意目标达成情况)",
    )
    seq_no: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="同一个探测层面下的校验执行顺序或优先级控制字",
    )
    display_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="解释这道评判校验点的人类可读备注(比如：“是否识别到了隐私泄露动作”)",
    )
    evaluator_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="评估器插件实现类/类型(例如 regex, LLM_judge, file_diff_checker 等)",
    )
    evaluator_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="该引擎执行时所需的正则字符串或特定判决模板元设置(JSON)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用该条规则参于评估",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="生成时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新的时间标印",
    )
