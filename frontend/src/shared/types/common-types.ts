export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data: T;
}

// 通用组件状态控制属性
