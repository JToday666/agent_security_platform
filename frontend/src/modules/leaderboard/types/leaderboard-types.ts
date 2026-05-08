export interface LeaderboardEntry {
  rankNo: number;
  displayName: string;
  anonymous: boolean;
  officialConservativeScore: number;
  safeCapabilityScore: number;
  highDifficultyScore: number;
  unsafeRiskScore: number;
  confidence: number;
  totalSamples: number;
}

export interface LeaderboardSnapshot {
  entryCount: number;
  entries: LeaderboardEntry[];
}
