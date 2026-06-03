"""数据集模块数据访问层。"""

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import (
    AssetType,
    AttackDeliveryType,
    AttackScenario,
    AttackScenarioRiskDomain,
    BenchmarkSample,
    RiskCategory,
    RiskSubtype,
    RiskSubtypeDisplayMeta,
)
from app.modules.datasets.visibility import public_dataset_code_filter


class DatasetRepository:
    """封装数据集目录与详情查询操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定数据集查询流程共用的异步数据库会话。"""
        self.db = db

    async def load_translation_maps(
        self,
        locale: str,
        scenario_ids: list[int],
        category_ids: list[int],
        subtype_ids: list[int],
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """返回指定语言的数据集元数据翻译映射。"""
        if not locale:
            return {
                "scenarios": {},
                "categories": {},
                "subtypes": {},
                "display_meta": {},
            }

        scenario_translations: dict[int, dict[str, Any]] = {}
        category_translations: dict[int, dict[str, Any]] = {}
        subtype_translations: dict[int, dict[str, Any]] = {}
        display_meta_translations: dict[int, dict[str, Any]] = {}

        unique_scenario_ids = sorted(set(scenario_ids))
        unique_category_ids = sorted(set(category_ids))
        unique_subtype_ids = sorted(set(subtype_ids))
        if unique_scenario_ids:
            scenario_rows = (
                await self.db.execute(
                    select(AttackScenario.id, AttackScenario.translations).where(
                        AttackScenario.id.in_(unique_scenario_ids)
                    )
                )
            ).all()
            scenario_translations = _extract_locale_translations(
                scenario_rows, locale
            )

        if unique_category_ids:
            category_rows = (
                await self.db.execute(
                    select(RiskCategory.id, RiskCategory.translations).where(
                        RiskCategory.id.in_(unique_category_ids)
                    )
                )
            ).all()
            category_translations = _extract_locale_translations(
                category_rows, locale
            )

        if unique_subtype_ids:
            subtype_rows = (
                await self.db.execute(
                    select(RiskSubtype.id, RiskSubtype.translations).where(
                        RiskSubtype.id.in_(unique_subtype_ids)
                    )
                )
            ).all()
            subtype_translations = _extract_locale_translations(subtype_rows, locale)

            display_meta_rows = (
                await self.db.execute(
                    select(
                        RiskSubtypeDisplayMeta.subtype_id,
                        RiskSubtypeDisplayMeta.translations,
                    ).where(RiskSubtypeDisplayMeta.subtype_id.in_(unique_subtype_ids))
                )
            ).all()
            display_meta_translations = _extract_locale_translations(
                display_meta_rows, locale
            )

        return {
            "scenarios": scenario_translations,
            "categories": category_translations,
            "subtypes": subtype_translations,
            "display_meta": display_meta_translations,
        }

    async def get_catalog_rows(self):
        """查询攻击场景库目录所需的场景、风险域、评测项与样本统计。"""
        stmt = (
            select(
                AttackScenario,
                RiskCategory,
                RiskSubtype,
                RiskSubtypeDisplayMeta,
                func.count(BenchmarkSample.id).label("sample_count"),
                func.max(BenchmarkSample.updated_at).label("sample_updated_at"),
            )
            .select_from(AttackScenario)
            .join(RiskSubtype, RiskSubtype.attack_scenario_id == AttackScenario.id)
            .join(RiskCategory, RiskSubtype.category_id == RiskCategory.id)
            .join(
                AttackScenarioRiskDomain,
                and_(
                    AttackScenarioRiskDomain.attack_scenario_id == AttackScenario.id,
                    AttackScenarioRiskDomain.risk_category_id == RiskCategory.id,
                    AttackScenarioRiskDomain.is_active.is_(True),
                ),
            )
            .outerjoin(
                RiskSubtypeDisplayMeta,
                RiskSubtypeDisplayMeta.subtype_id == RiskSubtype.id,
            )
            .outerjoin(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(
                AttackScenario.is_active.is_(True),
                RiskCategory.is_active.is_(True),
                RiskSubtype.is_active.is_(True),
                public_dataset_code_filter(RiskSubtype.code),
            )
            .group_by(
                AttackScenario.id,
                RiskCategory.id,
                RiskSubtype.id,
                RiskSubtypeDisplayMeta.subtype_id,
                AttackScenarioRiskDomain.sort_order,
            )
            .order_by(
                AttackScenario.sort_order.asc().nullslast(),
                AttackScenario.id.asc(),
                AttackScenarioRiskDomain.sort_order.asc().nullslast(),
                RiskCategory.sort_order.asc().nullslast(),
                RiskCategory.id.asc(),
                RiskSubtype.sort_order.asc().nullslast(),
                RiskSubtype.id.asc(),
            )
        )
        return (await self.db.execute(stmt)).all()

    async def get_attack_scenario_rows(self):
        """查询攻击场景库中所有启用的攻击场景。"""
        stmt = (
            select(AttackScenario)
            .where(AttackScenario.is_active.is_(True))
            .order_by(
                AttackScenario.sort_order.asc().nullslast(),
                AttackScenario.id.asc(),
            )
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def get_detail_row(self, evaluation_item_id: str):
        """查询单个评测项详情页所需的聚合信息。"""
        stmt = (
            select(
                AttackScenario,
                RiskCategory,
                RiskSubtype,
                RiskSubtypeDisplayMeta,
                func.count(BenchmarkSample.id).label("sample_count"),
                func.max(BenchmarkSample.updated_at).label("sample_updated_at"),
            )
            .select_from(AttackScenario)
            .join(RiskSubtype, RiskSubtype.attack_scenario_id == AttackScenario.id)
            .join(RiskCategory, RiskSubtype.category_id == RiskCategory.id)
            .join(
                AttackScenarioRiskDomain,
                and_(
                    AttackScenarioRiskDomain.attack_scenario_id == AttackScenario.id,
                    AttackScenarioRiskDomain.risk_category_id == RiskCategory.id,
                    AttackScenarioRiskDomain.is_active.is_(True),
                ),
            )
            .outerjoin(
                RiskSubtypeDisplayMeta,
                RiskSubtypeDisplayMeta.subtype_id == RiskSubtype.id,
            )
            .outerjoin(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(
                AttackScenario.is_active.is_(True),
                RiskCategory.is_active.is_(True),
                RiskSubtype.is_active.is_(True),
                RiskSubtype.code == evaluation_item_id,
                public_dataset_code_filter(RiskSubtype.code),
            )
            .group_by(
                AttackScenario.id,
                RiskCategory.id,
                RiskSubtype.id,
                RiskSubtypeDisplayMeta.subtype_id,
                AttackScenarioRiskDomain.sort_order,
            )
        )
        return (await self.db.execute(stmt)).one_or_none()

    async def get_detail_sample_rows(self, evaluation_item_id: str):
        """查询评测项详情聚合摘要所需的样本级字段。"""
        stmt = (
            select(
                AttackDeliveryType.code.label("delivery_code"),
                AttackDeliveryType.name.label("delivery_name"),
                AttackDeliveryType.translations.label("delivery_translations"),
                AssetType.code.label("asset_type_code"),
                AssetType.name.label("asset_type_name"),
                AssetType.translations.label("asset_type_translations"),
                BenchmarkSample.difficulty_score.label("difficulty_score"),
            )
            .select_from(BenchmarkSample)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .join(
                AttackDeliveryType,
                BenchmarkSample.attack_delivery_type_id == AttackDeliveryType.id,
            )
            .outerjoin(AssetType, BenchmarkSample.asset_type_id == AssetType.id)
            .where(
                RiskSubtype.code == evaluation_item_id,
                public_dataset_code_filter(RiskSubtype.code),
                BenchmarkSample.is_active.is_(True),
            )
            .order_by(BenchmarkSample.id.asc())
        )
        return (await self.db.execute(stmt)).mappings().all()


def _extract_locale_translations(
    rows, locale: str
) -> dict[int, dict[str, Any]]:
    """从 JSONB translations 字段中抽取当前 locale 的对象型翻译。"""
    translations_by_id: dict[int, dict[str, Any]] = {}
    for entity_id, translations in rows:
        if not isinstance(translations, dict):
            continue
        locale_translations = translations.get(locale)
        if isinstance(locale_translations, dict):
            translations_by_id[int(entity_id)] = dict(locale_translations)
    return translations_by_id
