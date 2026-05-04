export interface LeaderboardEntry {
  rankNo: number;
  agentId: string;
  agentName: string;
  evaluationId: string;
  officialConservativeScore: number;
  safeCapabilityScore: number;
  highDifficultyScore: number;
  unsafeRiskScore: number;
  confidence: number;
  verificationTier: string;
  safetyCertification: string;
  totalSamples: number;
}

export interface LeaderboardSnapshot {
  snapshotCode: string;
  entryCount: number;
  entries: LeaderboardEntry[];
}
