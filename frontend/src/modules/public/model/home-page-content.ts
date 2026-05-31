import { RouteLocation } from "@/app/router/route-names";
import type {
  HomeInfoSection,
  HomeSectionJumpConfig,
  HomeSectionKey,
  WorkflowItem,
} from "./home-page-types";

type HomeTranslator = (key: string) => string;

export const HOME_SECTION_KEYS: readonly HomeSectionKey[] = [
  "quickstart",
  "capabilities",
  "loop",
  "trust",
  "aegis",
  "experience",
] as const;

export const buildSectionJumpMap = (
  t: HomeTranslator,
): Record<HomeSectionKey, HomeSectionJumpConfig> => ({
  quickstart: {
    key: "quickstart",
    title: t("public.home.quickstart.title"),
    description: t("public.home.quickstart.description"),
  },
  capabilities: {
    key: "capabilities",
    title: t("public.home.sections.capabilities.kicker"),
    description: t("public.home.sections.capabilities.title"),
  },
  loop: {
    key: "loop",
    title: t("public.home.sections.loop.kicker"),
    description: t("public.home.sections.loop.title"),
  },
  trust: {
    key: "trust",
    title: t("public.home.sections.trust.kicker"),
    description: t("public.home.sections.trust.title"),
  },
  aegis: {
    key: "aegis",
    title: t("public.home.sections.aegis.kicker"),
    description: t("public.home.sections.aegis.title"),
  },
  experience: {
    key: "experience",
    title: t("public.home.sections.experience.kicker"),
    description: t("public.home.sections.experience.title"),
  },
});

export const buildWorkflowItems = (
  t: HomeTranslator,
  isLogin: boolean,
): WorkflowItem[] => [
  {
    step: 1,
    icon: "app:home.workflow.browse",
    title: t("public.home.workflow.browse.title"),
    description: t("public.home.workflow.browse.description"),
    actionLabel: t("public.home.workflow.browse.action"),
    to: RouteLocation.datasetList,
  },
  {
    step: 2,
    icon: "app:home.workflow.submit",
    title: t("public.home.workflow.submit.title"),
    description: t("public.home.workflow.submit.description"),
    actionLabel: isLogin
      ? t("public.home.workflow.submit.actionAuthed")
      : t("public.home.workflow.submit.actionGuest"),
    to: isLogin ? RouteLocation.agentSubmit : RouteLocation.datasetList,
  },
  {
    step: 3,
    icon: "app:home.workflow.track",
    title: t("public.home.workflow.track.title"),
    description: t("public.home.workflow.track.description"),
    actionLabel: isLogin
      ? t("public.home.workflow.track.actionAuthed")
      : t("public.home.workflow.track.actionGuest"),
    to: isLogin ? RouteLocation.userCenter : RouteLocation.contact,
  },
  {
    step: 4,
    icon: "app:home.workflow.review",
    title: t("public.home.workflow.review.title"),
    description: t("public.home.workflow.review.description"),
    actionLabel: isLogin
      ? t("public.home.workflow.review.actionAuthed")
      : t("public.home.workflow.review.actionGuest"),
    to: isLogin ? RouteLocation.userCenter : RouteLocation.contact,
  },
];

export const buildIntroSections = (
  t: HomeTranslator,
  isLogin: boolean,
): HomeInfoSection[] => [
  {
    key: "capabilities",
    kind: "cards",
    description: t("public.home.sections.capabilities.description"),
    items: [
      {
        key: "datasets",
        icon: "app:home.section.dataset",
        title: t("public.home.sections.capabilities.items.datasets.title"),
        description: t(
          "public.home.sections.capabilities.items.datasets.description",
        ),
      },
      {
        key: "evaluation",
        icon: "app:home.section.evaluation",
        title: t("public.home.sections.capabilities.items.evaluation.title"),
        description: t(
          "public.home.sections.capabilities.items.evaluation.description",
        ),
      },
      {
        key: "report",
        icon: "app:home.section.report",
        title: t("public.home.sections.capabilities.items.report.title"),
        description: t(
          "public.home.sections.capabilities.items.report.description",
        ),
      },
      {
        key: "ranking",
        icon: "app:home.section.ranking",
        title: t("public.home.sections.capabilities.items.ranking.title"),
        description: t(
          "public.home.sections.capabilities.items.ranking.description",
        ),
      },
    ],
  },
  {
    key: "loop",
    kind: "loop",
    description: t("public.home.sections.loop.description"),
    items: [
      {
        key: "scope",
        icon: "app:home.section.scope",
        title: t("public.home.sections.loop.items.scope.title"),
        description: t("public.home.sections.loop.items.scope.description"),
      },
      {
        key: "submit",
        icon: "app:home.section.submit",
        title: t("public.home.sections.loop.items.submit.title"),
        description: t("public.home.sections.loop.items.submit.description"),
      },
      {
        key: "evidence",
        icon: "app:home.section.evidence",
        title: t("public.home.sections.loop.items.evidence.title"),
        description: t("public.home.sections.loop.items.evidence.description"),
      },
    ],
  },
  {
    key: "trust",
    kind: "trust",
    description: t("public.home.sections.trust.description"),
    items: [
      {
        key: "standard",
        icon: "app:home.section.standard",
        title: t("public.home.sections.trust.items.standard.title"),
        description: t("public.home.sections.trust.items.standard.description"),
      },
      {
        key: "privacy",
        icon: "app:home.section.privacy",
        title: t("public.home.sections.trust.items.privacy.title"),
        description: t("public.home.sections.trust.items.privacy.description"),
      },
      {
        key: "confidence",
        icon: "app:home.section.confidence",
        title: t("public.home.sections.trust.items.confidence.title"),
        description: t("public.home.sections.trust.items.confidence.description"),
      },
    ],
  },
  {
    key: "aegis",
    kind: "aegis",
    description: t("public.home.sections.aegis.description"),
    expansion: t("public.home.sections.aegis.expansion"),
    story: [
      t("public.home.sections.aegis.story.guardian"),
      t("public.home.sections.aegis.story.platform"),
    ],
    items: [],
  },
  {
    key: "experience",
    kind: "experience",
    description: t("public.home.sections.experience.description"),
    items: [
      {
        key: "catalog",
        icon: "app:home.section.dataset",
        title: t("public.home.sections.experience.items.catalog.title"),
        description: t("public.home.sections.experience.items.catalog.description"),
        actionLabel: t("common.actions.browseDataset"),
        to: RouteLocation.datasetList,
      },
      {
        key: "submit",
        icon: "app:home.section.submit",
        title: t("public.home.sections.experience.items.submit.title"),
        description: t("public.home.sections.experience.items.submit.description"),
        actionLabel: isLogin
          ? t("common.actions.submitEvaluation")
          : t("public.home.workflow.submit.actionGuest"),
        to: isLogin ? RouteLocation.agentSubmit : RouteLocation.datasetList,
      },
      {
        key: "leaderboard",
        icon: "app:home.section.ranking",
        title: t("public.home.sections.experience.items.leaderboard.title"),
        description: t(
          "public.home.sections.experience.items.leaderboard.description",
        ),
        actionLabel: t("layout.nav.leaderboard"),
        to: RouteLocation.leaderboard,
      },
      {
        key: "contact",
        icon: "app:home.section.contact",
        title: t("public.home.sections.experience.items.contact.title"),
        description: t("public.home.sections.experience.items.contact.description"),
        actionLabel: t("common.actions.contactUs"),
        to: RouteLocation.contact,
      },
    ],
  },
];
