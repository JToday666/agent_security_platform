export type SubmitMethod = "api" | "docker";
export type LeaderboardDisplayMode = "public" | "anonymous";
export type LeaderboardVisibilityStatus = LeaderboardDisplayMode | "unranked";
export type EvaluationStatus =
  | "queued"
  | "pending"
  | "running"
  | "pausing"
  | "paused"
  | "terminating"
  | "canceling"
  | "completed"
  | "terminated"
  | "canceled"
  | "failed";

export type EvaluationFinalizationReason =
  | "completed"
  | "terminated_by_user"
  | "auto_terminated_after_pause_timeout"
  | "canceled_by_user"
  | "failed";

export type EvaluationAction = "pause" | "resume" | "terminate" | "cancel";
export type EvaluationSampleOutcome = "success" | "failed" | "error";
export type EvaluationScoreTrendScope = "recent10" | "all";
export type EvaluationScoreTrendView = "capability" | "risk";
export type EvaluationScoreMetricKey =
  | "conservativeScore"
  | "performanceScore"
  | "confidence"
  | "completionScore"
  | "safetyScore"
  | "hardScore"
  | "unsafeRate"
  | "timeScore";

export type EvaluationScoreMap = Partial<
  Record<EvaluationScoreMetricKey, number>
>;
export type EvaluationReportScores = Record<EvaluationScoreMetricKey, number>;

export interface SubmitParameters {
  difficulty: number;
  timeoutMinutes: number;
  maxSteps: number;
  retryEnabled?: boolean;
}

export interface SubmitDockerPayload {
  imageUri: string;
  command: string;
  env: Record<string, string>;
}

export interface SubmitAgentPayload {
  submitMethod: SubmitMethod;
  agentId?: string | null;
  docker?: SubmitDockerPayload | null;
  parameters: SubmitParameters;
  leaderboardDisplayMode: LeaderboardDisplayMode;
  selectedDatasetIds: string[];
  requestId: string;
}

export interface RangeMeta {
  min: number;
  max: number;
  step: number;
  default: number;
  recommendedMax?: number;
}

export interface BooleanMeta {
  default: boolean;
}

export interface LeaderboardDisplayModeMeta {
  default: LeaderboardDisplayMode;
  options: LeaderboardDisplayMode[];
}

export interface SubmitMetaResponse {
  supportedMethods: SubmitMethod[];
  difficulty: RangeMeta;
  timeoutMinutes: RangeMeta;
  maxSteps: RangeMeta;
  publicToLeaderboard?: BooleanMeta;
  leaderboardDisplayMode: LeaderboardDisplayModeMeta;
}

export interface PrecheckResponse {
  ok: boolean;
  warnings: string[];
}

export interface SubmitResponse {
  evaluationId: string;
  status: EvaluationStatus;
  createdAt: string;
}

export interface PendingSubmitRequest {
  requestId: string;
  payloadDigest: string;
  createdAt: string;
}

export interface SubmitFieldErrors {
  agentId?: string;
  docker?: string;
  selectedDatasetIds?: string;
  requestId?: string;
}

export interface EvaluationRecord {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  finishedAt?: string | null;
  status: EvaluationStatus;
  progressPercent: number;
  finalReportAvailable: boolean;
  finalizationReason: EvaluationFinalizationReason | null;
  publicToLeaderboard: boolean;
  leaderboardDisplayMode: LeaderboardDisplayMode;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: SubmitMethod;
  score: number | null;
  ownerName: string;
  parameters: SubmitParameters;
  sampleSummary?: EvaluationSampleSummary | null;
}

export interface EvaluationMetric {
  name: string;
  value: string;
  percentage: number;
  description: string;
}

export interface EvaluationReportRiskCategoryItem {
  categoryId: string;
  name: string;
  totalSamples: number;
  taskCompletedCount: number;
  harmDetectedCount: number;
}

export interface EvaluationReportLevelItem {
  level: number;
  totalSamples: number;
  harmDetectedCount: number;
}

export interface EvaluationProgress {
  percent: number;
  totalDatasetCount: number;
  completedDatasetCount: number;
  totalSampleCount?: number;
  completedSampleCount?: number;
  runningDatasetId: string | null;
  runningDatasetName: string | null;
  pauseDeadlineAt: string | null;
  statusText: string;
}

export interface EvaluationControls {
  canPause: boolean;
  canResume: boolean;
  canTerminate: boolean;
  canCancel: boolean;
  pauseUsed: boolean;
}

export interface EvaluationReport {
  reportStatus: string;
  summary: {
    totalSamples: number;
    completedSamples: number;
    taskCompletedCount: number;
    harmDetectedCount: number;
    failedCount: number;
    byRiskCategory: EvaluationReportRiskCategoryItem[];
    byRiskLevel: EvaluationReportLevelItem[];
    byAttackLevel: EvaluationReportLevelItem[];
  };
  reportUri: string | null;
  generatedAt: string;
  warnings: string[];
  metrics: EvaluationMetric[];
}

export interface EvaluationSampleSummary {
  total: number;
  success: number;
  failed: number;
  error: number;
}

export interface EvaluationRepresentativeSample {
  sampleId: string;
  datasetName: string;
  normalizedResult: EvaluationSampleOutcome;
  outcomeReasonText: string;
  replayUrl: string | null;
}

export interface EvaluationRepresentativeSamples {
  success: EvaluationRepresentativeSample | null;
  failed: EvaluationRepresentativeSample | null;
  error: EvaluationRepresentativeSample | null;
}

export interface EvaluationDownloads {
  sampleDetailsUrl: string | null;
}

export interface EvaluationTrendViewConfig {
  label: string;
  metrics: EvaluationScoreMetricKey[];
}

export interface EvaluationScoreTrendItem {
  evaluationId: string;
  agentName: string;
  createdAt: string;
  finishedAt: string | null;
  scores: EvaluationScoreMap;
}

export interface EvaluationScoreTrend {
  scope: EvaluationScoreTrendScope;
  defaultScope: EvaluationScoreTrendScope;
  defaultView: EvaluationScoreTrendView;
  views: Record<EvaluationScoreTrendView, EvaluationTrendViewConfig>;
  items: EvaluationScoreTrendItem[];
}

export interface EvaluationReportRawStats extends EvaluationSampleSummary {
  completionRate: number;
  successRate: number;
  conditionalSuccessRate: number;
}

export interface EvaluationReportPosteriorInterval {
  psQ05: number;
  psQ50: number;
  psQ95: number;
}

export interface EvaluationReportCoverage {
  difficultyBucketHitCount: number;
  difficultyCoverageRatio: number;
}

export interface EvaluationReportDifficultyBucket {
  bucket: string;
  total: number;
  success: number;
  failed: number;
  error: number;
  successRate: number;
}

export interface EvaluationReportDatasetSummary {
  datasetId: string;
  datasetName: string;
  total: number;
  success: number;
  failed: number;
  error: number;
}

export interface EvaluationReportScatterPoint {
  sampleId: string;
  difficulty: number;
  durationMs: number;
  normalizedResult: EvaluationSampleOutcome;
}

export interface EvaluationReportBreakdowns {
  outcomeSummary: EvaluationSampleSummary;
  difficultyBuckets: EvaluationReportDifficultyBucket[];
  datasetSummaries: EvaluationReportDatasetSummary[];
  sampleScatterPoints: EvaluationReportScatterPoint[];
}

export interface EvaluationReportVersions {
  difficultyVersion: string;
  scoreModelVersion: string;
  benchmarkVersion: string;
}

export interface EvaluationReportPayload {
  evaluationId: string;
  status: string;
  generatedAt: string;
  scores: EvaluationReportScores;
  rawStats: EvaluationReportRawStats;
  posteriorInterval: EvaluationReportPosteriorInterval;
  coverage: EvaluationReportCoverage;
  breakdowns: EvaluationReportBreakdowns;
  versions: EvaluationReportVersions;
}

export interface EvaluationDetail extends Omit<
  EvaluationRecord,
  "progressPercent"
> {
  startedAt: string | null;
  finishedAt: string | null;
  progress: EvaluationProgress;
  controls: EvaluationControls;
  report: EvaluationReport | null;
  sampleSummary: EvaluationSampleSummary | null;
  representativeSamples: EvaluationRepresentativeSamples;
  downloads: EvaluationDownloads;
}

export interface EvaluationActionRequest {
  action: EvaluationAction;
}

export interface SubmitFormState {
  submitMethod: SubmitMethod;
  agentId: string;
  docker: {
    imageUri: string;
    command: string;
  };
  parameters: SubmitParameters;
  leaderboardDisplayMode: LeaderboardDisplayMode;
  selectedDatasetIds: string[];
}
