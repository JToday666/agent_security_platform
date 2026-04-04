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

// 通用组件状态控制属性
export interface StateControlProps {
  loading?: boolean;
  disabled?: boolean;
  error?: string;
}
