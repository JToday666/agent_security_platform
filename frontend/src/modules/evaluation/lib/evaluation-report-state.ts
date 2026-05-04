const REPORT_UNAVAILABLE_MESSAGE =
  "报告详情暂不可用。当前可查看评测摘要，完整报告接口接入后将展示评分、样本分布和版本信息。";

export const isReportEndpointUnavailableError = (value: unknown): boolean => {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as { code?: unknown; httpStatus?: unknown };
  return (
    Number(candidate.code) === 40400 || Number(candidate.httpStatus) === 404
  );
};

export const getReportUnavailableMessage = (): string =>
  REPORT_UNAVAILABLE_MESSAGE;
