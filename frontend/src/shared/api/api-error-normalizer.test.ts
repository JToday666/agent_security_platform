import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  resetRuntimeTranslator,
  setRuntimeTranslator,
} from "@/app/i18n/runtime-translator";
import { extractErrorMessage } from "@/shared/api/api-error-normalizer";

const serviceUnavailableMessage = "服务暂时不可用，请稍后重试。";

describe("api-error-normalizer", () => {
  beforeEach(() => {
    setRuntimeTranslator((key) =>
      key === "network.errors.serviceUnavailable"
        ? serviceUnavailableMessage
        : key,
    );
  });

  afterEach(() => {
    resetRuntimeTranslator();
  });

  it("hides nginx html error pages returned with text/html content type", () => {
    const message = extractErrorMessage(
      "<html><head><title>502 Bad Gateway</title></head><body>nginx</body></html>",
      {
        httpStatus: 502,
        contentType: "text/html; charset=utf-8",
      },
    );

    expect(message).toBe(serviceUnavailableMessage);
  });

  it("hides html-looking gateway bodies without relying on content type", () => {
    const message = extractErrorMessage(" \n<!doctype html><html></html>", {
      httpStatus: 503,
    });

    expect(message).toBe(serviceUnavailableMessage);
  });

  it("localizes nginx json error payloads that carry a message key", () => {
    const message = extractErrorMessage(
      {
        code: 10502,
        message: "service_unavailable",
        messageKey: "network.errors.serviceUnavailable",
        data: { requestId: "req-1" },
      },
      {
        httpStatus: 502,
        contentType: "application/json",
      },
    );

    expect(message).toBe(serviceUnavailableMessage);
  });

  it("keeps ordinary backend business error messages", () => {
    const message = extractErrorMessage(
      {
        code: 40001,
        message: "用户名或密码错误",
      },
      {
        httpStatus: 400,
        contentType: "application/json",
      },
    );

    expect(message).toBe("用户名或密码错误");
  });

  it("uses the service unavailable message for empty gateway responses", () => {
    const message = extractErrorMessage("", { httpStatus: 504 });

    expect(message).toBe(serviceUnavailableMessage);
  });
});
