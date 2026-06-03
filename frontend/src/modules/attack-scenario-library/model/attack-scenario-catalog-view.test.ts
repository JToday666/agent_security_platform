import { describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  ATTACK_SCENARIO_ALL_ID,
  buildAttackScenarioCatalogView,
  RISK_DOMAIN_ALL_ID,
} from "@/modules/attack-scenario-library/model/attack-scenario-catalog-view";
import { useAttackScenarioCatalogStore } from "@/modules/attack-scenario-library/stores/attackScenarioCatalogStore";
import { useSubmitAttackScenarioCatalog } from "@/modules/submission/composables/useSubmitAttackScenarioCatalog";
import type { AttackScenarioCatalogItem } from "@/shared/types/attack-scenario-library-types";

const catalog: AttackScenarioCatalogItem[] = [
  {
    attackScenarioId: "prompt_injection",
    name: "提示注入",
    sort: 1,
    enabled: true,
    riskDomainCount: 2,
    evaluationItemCount: 3,
    sampleCount: 474,
    riskDomains: [
      {
        riskDomainId: "confidentiality",
        name: "机密性",
        meaning: "敏感信息保护与最小暴露。",
        description: "面向验证码、身份信息和凭证密钥等敏感资产的泄露风险。",
        sort: 1,
        enabled: true,
        evaluationItemCount: 2,
        sampleCount: 417,
        evaluationItems: [
          {
            evaluationItemId: "internal-a",
            name: "身份信息泄露",
            shortDescription: "评估代理保护姓名和验证码的能力。",
            sampleCount: 150,
            updatedAt: "2026-03-20T00:00:00Z",
            enabled: true,
          },
          {
            evaluationItemId: "internal-b",
            name: "凭证与密钥泄露",
            shortDescription: "评估代理保护 API key 和 SSH 凭据的能力。",
            sampleCount: 267,
            updatedAt: "2026-03-21T00:00:00Z",
            enabled: true,
          },
        ],
      },
      {
        riskDomainId: "integrity",
        name: "完整性",
        meaning: "关键内容和文件不可篡改。",
        description: "面向文件、表单和系统配置被代理误改的风险。",
        sort: 2,
        enabled: true,
        evaluationItemCount: 1,
        sampleCount: 57,
        evaluationItems: [
          {
            evaluationItemId: "internal-c",
            name: "本地文件篡改",
            shortDescription: "评估代理是否会被诱导修改本地文件。",
            sampleCount: 57,
            updatedAt: "2026-03-22T00:00:00Z",
            enabled: true,
          },
        ],
      },
    ],
  },
];

const emptyScenario: AttackScenarioCatalogItem = {
  attackScenarioId: "knowledge_base_poisoning",
  name: "知识库投毒",
  sort: 3,
  enabled: true,
  riskDomainCount: 0,
  evaluationItemCount: 0,
  sampleCount: 0,
  riskDomains: [],
};

describe("buildAttackScenarioCatalogView", () => {
  it("summarizes the full catalog and sorts evaluation items by sample count", () => {
    const view = buildAttackScenarioCatalogView(
      catalog,
      ATTACK_SCENARIO_ALL_ID,
      RISK_DOMAIN_ALL_ID,
      "",
      "samples-desc",
    );

    expect(view.summary).toEqual({
      attackScenarioCount: 1,
      riskDomainCount: 2,
      evaluationItemCount: 3,
      sampleCount: 474,
      updatedAt: "2026-03-22T00:00:00Z",
    });
    expect(view.results.map((item) => item.name)).toEqual([
      "凭证与密钥泄露",
      "身份信息泄露",
      "本地文件篡改",
    ]);
  });

  it("filters by active risk domain and includes risk domain metadata in search", () => {
    const activeCategoryView = buildAttackScenarioCatalogView(
      catalog,
      ATTACK_SCENARIO_ALL_ID,
      "integrity",
      "",
      "samples-desc",
    );

    expect(activeCategoryView.results.map((item) => item.name)).toEqual([
      "本地文件篡改",
    ]);

    const categorySearchView = buildAttackScenarioCatalogView(
      catalog,
      ATTACK_SCENARIO_ALL_ID,
      RISK_DOMAIN_ALL_ID,
      "最小暴露",
      "samples-desc",
    );

    expect(categorySearchView.results.map((item) => item.name)).toEqual([
      "凭证与密钥泄露",
      "身份信息泄露",
    ]);
  });

  it("keeps empty active attack scenarios selectable in catalog views", () => {
    const view = buildAttackScenarioCatalogView(
      [...catalog, emptyScenario],
      "knowledge_base_poisoning",
      RISK_DOMAIN_ALL_ID,
      "",
      "samples-desc",
    );

    expect(view.activeAttackScenario?.attackScenarioId).toBe(
      "knowledge_base_poisoning",
    );
    expect(view.filters).toHaveLength(1);
    expect(view.filters[0]).toMatchObject({
      riskDomainId: RISK_DOMAIN_ALL_ID,
      count: 0,
      sampleCount: 0,
    });
    expect(view.results).toEqual([]);
    expect(view.summary.attackScenarioCount).toBe(2);
  });

  it("keeps empty active attack scenarios in shared frontend catalogs", () => {
    setActivePinia(createPinia());
    const store = useAttackScenarioCatalogStore();
    store.attackScenarios = [...catalog, emptyScenario];
    const submitCatalog = useSubmitAttackScenarioCatalog();
    submitCatalog.catalog.value = {
      catalogVersion: "2026-06-03T00:00:00Z",
      attackScenarioCount: 2,
      riskDomainCount: 2,
      evaluationItemCount: 3,
      attackScenarios: [...catalog, emptyScenario],
    };

    expect(
      store.enabledAttackScenarios.map((scenario) => scenario.attackScenarioId),
    ).toContain("knowledge_base_poisoning");
    expect(
      submitCatalog.enabledAttackScenarios.value.map(
        (scenario) => scenario.attackScenarioId,
      ),
    ).toContain("knowledge_base_poisoning");
  });
});
