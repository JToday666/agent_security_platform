import type { RouteLocationRaw } from "vue-router";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export type HomeSectionKey =
  | "quickstart"
  | "capabilities"
  | "loop"
  | "trust"
  | "aegis"
  | "experience";

export type HomeInfoSectionKey = Exclude<HomeSectionKey, "quickstart">;

export interface WorkflowItem {
  step: number;
  icon: AppIconName;
  title: string;
  description: string;
  actionLabel: string;
  to: RouteLocationRaw;
}

export interface HomeSectionJumpConfig {
  key: HomeSectionKey;
  title: string;
  description: string;
}

export interface HomeSectionItem {
  key: string;
  icon: AppIconName;
  title: string;
  description: string;
  actionLabel?: string;
  to?: RouteLocationRaw;
}

export interface HomeInfoSection {
  key: HomeInfoSectionKey;
  kind: "cards" | "loop" | "trust" | "aegis" | "experience";
  description: string;
  items: HomeSectionItem[];
  expansion?: string;
  story?: string[];
}

export interface HomeInfoSectionWithJump {
  jump: HomeSectionJumpConfig;
  section: HomeInfoSection;
}
