import { DEFAULT_LOCALE, normalizeLocale } from "@/app/i18n";

// 统一维护路由名称与命名路由跳转对象，避免页面内散落硬编码路径。
export const ROUTE_NAME = {
  HOME_PAGE: "HomePage",
  DATASET_LIST: "DatasetList",
  DATASET_DETAIL: "DatasetDetail",
  LEADERBOARD_PAGE: "LeaderboardPage",
  CONTACT_PAGE: "ContactPage",
  NOT_FOUND: "NotFoundPage",
  USER_CENTER: "UserCenter",
  EVALUATION_DETAIL: "EvaluationDetail",
  AGENT_MANAGEMENT: "AgentManagement",
  AGENT_REGISTER: "AgentRegister",
  AGENT_DETAIL: "AgentDetail",
  AGENT_SUBMIT: "AgentSubmit",
  USER_PROFILE: "UserProfile",
} as const;

export type AppRouteName = (typeof ROUTE_NAME)[keyof typeof ROUTE_NAME];

export interface AppRouteLocation {
  name: AppRouteName;
  params: Record<string, string>;
  query?: Record<string, string | undefined>;
}

let currentLocale = DEFAULT_LOCALE;

const withLocaleParams = (
  params: Record<string, string> = {},
): Record<string, string> => ({
  locale: currentLocale,
  ...params,
});

const namedRoute = (
  name: AppRouteName,
  params: Record<string, string> = {},
  query?: Record<string, string | undefined>,
): AppRouteLocation => ({
  name,
  params: withLocaleParams(params),
  ...(query ? { query } : {}),
});

export const RouteLocation = {
  setCurrentLocale(locale: string) {
    currentLocale = normalizeLocale(locale);
  },

  get currentLocale() {
    return currentLocale;
  },

  get home() {
    return namedRoute(ROUTE_NAME.HOME_PAGE);
  },

  get datasetList() {
    return namedRoute(ROUTE_NAME.DATASET_LIST);
  },

  datasetDetail: (datasetId: string) =>
    namedRoute(ROUTE_NAME.DATASET_DETAIL, { datasetId }),

  get leaderboard() {
    return namedRoute(ROUTE_NAME.LEADERBOARD_PAGE);
  },

  get contact() {
    return namedRoute(ROUTE_NAME.CONTACT_PAGE);
  },

  get notFound() {
    return namedRoute(ROUTE_NAME.NOT_FOUND);
  },

  get userCenter() {
    return namedRoute(ROUTE_NAME.USER_CENTER);
  },

  evaluationDetail: (evaluationId: string) =>
    namedRoute(ROUTE_NAME.EVALUATION_DETAIL, { evaluationId }),

  get agentManagement() {
    return namedRoute(ROUTE_NAME.AGENT_MANAGEMENT);
  },

  agentRegister: (query?: { copyFrom?: string }) =>
    namedRoute(ROUTE_NAME.AGENT_REGISTER, {}, query),

  agentDetail: (agentId: string) =>
    namedRoute(ROUTE_NAME.AGENT_DETAIL, { agentId }),

  agentSubmitWithAgent: (agentId: string) =>
    namedRoute(ROUTE_NAME.AGENT_SUBMIT, {}, { agentId }),

  get agentSubmit() {
    return namedRoute(ROUTE_NAME.AGENT_SUBMIT);
  },

  get userProfile() {
    return namedRoute(ROUTE_NAME.USER_PROFILE);
  },
} as const;
