// 统一维护路由名称与命名路由跳转对象，避免页面内散落硬编码路径。
export const ROUTE_NAME = {
  HOME_PAGE: "HomePage",
  DATASET_LIST: "DatasetList",
  DATASET_DETAIL: "DatasetDetail",
  LEADERBOARD_PAGE: "LeaderboardPage",
  CONTACT_PAGE: "ContactPage",
  USER_CENTER: "UserCenter",
  EVALUATION_DETAIL: "EvaluationDetail",
  AGENT_SUBMIT: "AgentSubmit",
  USER_PROFILE: "UserProfile",
} as const;

export type AppRouteName = (typeof ROUTE_NAME)[keyof typeof ROUTE_NAME];

export const RouteLocation = {
  home: {
    name: ROUTE_NAME.HOME_PAGE,
  },
  datasetList: {
    name: ROUTE_NAME.DATASET_LIST,
  },
  datasetDetail: (datasetId: string) => ({
    name: ROUTE_NAME.DATASET_DETAIL,
    params: { datasetId },
  }),
  leaderboard: {
    name: ROUTE_NAME.LEADERBOARD_PAGE,
  },
  contact: {
    name: ROUTE_NAME.CONTACT_PAGE,
  },
  userCenter: {
    name: ROUTE_NAME.USER_CENTER,
  },
  evaluationDetail: (evaluationId: string) => ({
    name: ROUTE_NAME.EVALUATION_DETAIL,
    params: { evaluationId },
  }),
  agentSubmit: {
    name: ROUTE_NAME.AGENT_SUBMIT,
  },
  userProfile: {
    name: ROUTE_NAME.USER_PROFILE,
  },
} as const;
