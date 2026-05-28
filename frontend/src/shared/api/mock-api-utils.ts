import type { ApiEnvelope } from "@/shared/types/common-types";

interface MockOptions {
  delay?: number;
}

const cloneData = <T>(data: T): T => JSON.parse(JSON.stringify(data)) as T;

export const createSuccessEnvelope = <T>(
  data: T,
  message = "success",
): ApiEnvelope<T> => ({
  code: 0,
  message,
  data,
});

export const createErrorEnvelope = <T>(
  code: number,
  message: string,
  data: T,
): ApiEnvelope<T> => ({
  code,
  message,
  data,
});

export const resolveMockEnvelope = async <T>(
  envelope: ApiEnvelope<T>,
  options: MockOptions = {},
): Promise<ApiEnvelope<T>> => {
  const delay = options.delay ?? 360;
  await new Promise((resolve) => window.setTimeout(resolve, delay));
  return cloneData(envelope);
};
