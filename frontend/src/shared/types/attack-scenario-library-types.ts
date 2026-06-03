export interface EvaluationItemCatalogItem {
  evaluationItemId: string;
  name: string;
  shortDescription?: string | null;
  sampleCount?: number | null;
  updatedAt?: string | null;
  enabled: boolean;
}

export interface RiskDomainCatalogItem {
  riskDomainId: string;
  name: string;
  meaning?: string | null;
  description?: string | null;
  sort?: number | null;
  enabled: boolean;
  evaluationItemCount: number;
  sampleCount: number;
  evaluationItems: EvaluationItemCatalogItem[];
}

export interface AttackScenarioCatalogItem {
  attackScenarioId: string;
  name: string;
  description?: string | null;
  sort?: number | null;
  enabled: boolean;
  riskDomainCount: number;
  evaluationItemCount: number;
  sampleCount: number;
  riskDomains: RiskDomainCatalogItem[];
}

export interface AttackScenarioCatalogResponse {
  catalogVersion: string;
  attackScenarioCount: number;
  riskDomainCount: number;
  evaluationItemCount: number;
  attackScenarios: AttackScenarioCatalogItem[];
}

export interface EvaluationItemMediaItem {
  mediaId: string;
  type: "image" | "video";
  title: string;
  description?: string | null;
  url: string;
  coverUrl?: string | null;
  sort?: number | null;
}

export interface EvaluationItemResourceLink {
  label: string;
  url: string;
  type: "docs" | "download" | "demo" | "link";
}

export interface EvaluationItemDistributionItem {
  code: string;
  label: string;
  count: number;
  ratio: number;
}

export interface EvaluationItemSampleProfile {
  deliveryDistribution: EvaluationItemDistributionItem[];
  assetTypeTop: EvaluationItemDistributionItem[];
  difficultyBuckets: EvaluationItemDistributionItem[];
}

export interface EvaluationItemDetail {
  evaluationItemId: string;
  name: string;
  attackScenario: {
    attackScenarioId: string;
    name: string;
    description?: string | null;
  };
  riskDomain: {
    riskDomainId: string;
    name: string;
    meaning?: string | null;
  };
  shortDescription?: string | null;
  fullDescription?: string | null;
  sampleCount?: number | null;
  updatedAt?: string | null;
  highlights: string[];
  scenarios: string[];
  resources: EvaluationItemResourceLink[];
  media: EvaluationItemMediaItem[];
  sampleProfile: EvaluationItemSampleProfile;
}
