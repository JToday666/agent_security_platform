export interface ServiceError extends Error {
  code?: number;
}

export const createAgentServiceError = (
  message: string,
  code?: number,
): ServiceError => {
  const error = new Error(message) as ServiceError;
  error.code = code;
  return error;
};
