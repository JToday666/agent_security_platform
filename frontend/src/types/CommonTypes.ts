export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data: T;
}

export interface PersistedState<T> {
  version: number;
  savedAt: number;
  catalogVersion?: string;
  data: T;
}
