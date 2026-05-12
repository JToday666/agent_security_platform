import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";

export const isReportEndpointUnavailableError = (value: unknown): boolean => {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as { code?: unknown; httpStatus?: unknown };
  return (
    Number(candidate.code) === 40400 || Number(candidate.httpStatus) === 404
  );
};

export const getReportUnavailableMessage = (
  t: AppTranslator = translateRuntimeMessage,
): string => t("evaluation.report.unavailable");
