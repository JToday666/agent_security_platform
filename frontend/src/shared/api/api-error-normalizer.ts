import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";

export interface ApiValidationErrorItem {
  field: string;
  reason: string;
}

export interface ApiErrorMessageOptions {
  httpStatus?: number;
  contentType?: string;
}

interface LegacyValidationErrorItem {
  msg?: string;
  loc?: Array<string | number>;
}

const SERVICE_UNAVAILABLE_KEY = "network.errors.serviceUnavailable";
const htmlBodyPattern = /^\s*(?:<!doctype\s+html\b|<html\b)/i;
const gatewayUnavailableStatuses = new Set([502, 503, 504]);

const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);

const toTrimmedString = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const readRecord = (value: unknown): Record<string, unknown> | null =>
  isRecord(value) ? value : null;

const readMessageKey = (value: unknown): string => {
  const messageKey = toTrimmedString(value);
  if (!messageKey) {
    return "";
  }

  const translated = translateRuntimeMessage(messageKey);
  return translated && translated !== messageKey ? translated : "";
};

const serviceUnavailableMessage = (): string =>
  translateRuntimeMessage(SERVICE_UNAVAILABLE_KEY);

const isGatewayUnavailableStatus = (status?: number): boolean =>
  typeof status === "number" && gatewayUnavailableStatuses.has(status);

export const isHtmlErrorPayload = (
  payload: unknown,
  contentType?: string,
): boolean => {
  const normalizedContentType = contentType?.trim().toLowerCase() ?? "";
  if (normalizedContentType.startsWith("text/html")) {
    return true;
  }

  return typeof payload === "string" && htmlBodyPattern.test(payload);
};

const buildLegacyValidationMessage = (
  errors: LegacyValidationErrorItem[],
): string => {
  if (!errors.length) {
    return translateRuntimeMessage("network.validation.requestParameters");
  }

  return errors
    .map((item) => {
      const field =
        item.loc?.filter((value) => value !== "body").join(".") || "";
      return field
        ? `${field}: ${
            item.msg || translateRuntimeMessage("network.validation.parameter")
          }`
        : item.msg || translateRuntimeMessage("network.validation.parameter");
    })
    .join("；");
};

export const normalizeValidationErrors = (
  payload: unknown,
): ApiValidationErrorItem[] => {
  const record = readRecord(payload);
  const data = readRecord(record?.data);
  const candidateErrors = data?.errors;
  if (Array.isArray(candidateErrors)) {
    return candidateErrors
      .map((item) => {
        const errorRecord = readRecord(item);
        if (!errorRecord) {
          return null;
        }

        const field = toTrimmedString(errorRecord.field) || "request";
        const reason =
          toTrimmedString(errorRecord.reason) ||
          translateRuntimeMessage("network.validation.parameter");

        return { field, reason };
      })
      .filter((item): item is ApiValidationErrorItem => item !== null);
  }

  if (Array.isArray(record?.detail)) {
    return record.detail
      .map((item) => {
        const errorRecord = readRecord(item);
        if (!errorRecord) {
          return null;
        }

        const loc = Array.isArray(errorRecord.loc) ? errorRecord.loc : [];
        return {
          field: loc.filter((value) => value !== "body").join(".") || "request",
          reason:
            toTrimmedString(errorRecord.msg) ||
            translateRuntimeMessage("network.validation.parameter"),
        };
      })
      .filter((item): item is ApiValidationErrorItem => item !== null);
  }

  return [];
};

const buildValidationMessage = (errors: ApiValidationErrorItem[]): string => {
  if (!errors.length) {
    return translateRuntimeMessage("network.validation.requestParameters");
  }

  return errors
    .map((item) =>
      item.field && item.field !== "request"
        ? `${item.field}: ${item.reason}`
        : item.reason,
    )
    .join("；");
};

export const extractErrorMessage = (
  payload: unknown,
  options: ApiErrorMessageOptions = {},
): string => {
  if (isHtmlErrorPayload(payload, options.contentType)) {
    return serviceUnavailableMessage();
  }

  const record = readRecord(payload);
  const data = readRecord(record?.data);
  const translatedMessage =
    readMessageKey(record?.messageKey) || readMessageKey(data?.messageKey);
  if (translatedMessage) {
    return translatedMessage;
  }

  if (record) {
    const message = toTrimmedString(record.message);
    if (message) {
      return message;
    }

    const validationErrors = normalizeValidationErrors(record);
    if (validationErrors.length > 0) {
      return buildValidationMessage(validationErrors);
    }

    const detailMessage = toTrimmedString(record.detail);
    if (detailMessage) {
      return detailMessage;
    }

    const detailRecord = readRecord(record.detail);
    const nestedDetailMessage = toTrimmedString(detailRecord?.message);
    if (nestedDetailMessage) {
      return nestedDetailMessage;
    }

    if (Array.isArray(record.detail)) {
      const legacyErrors: LegacyValidationErrorItem[] = [];
      for (const item of record.detail) {
        const errorRecord = readRecord(item);
        if (!errorRecord) {
          continue;
        }

        legacyErrors.push({
          msg: toTrimmedString(errorRecord.msg) || undefined,
          loc: Array.isArray(errorRecord.loc)
            ? errorRecord.loc.filter(
                (value): value is string | number =>
                  typeof value === "string" || typeof value === "number",
              )
            : undefined,
        });
      }

      return buildLegacyValidationMessage(legacyErrors);
    }
  }

  if (isGatewayUnavailableStatus(options.httpStatus)) {
    return serviceUnavailableMessage();
  }

  const stringPayload = toTrimmedString(payload);
  if (stringPayload) {
    return stringPayload;
  }

  if (!payload) {
    return translateRuntimeMessage("network.errors.network");
  }

  return translateRuntimeMessage("network.errors.requestFailed");
};
