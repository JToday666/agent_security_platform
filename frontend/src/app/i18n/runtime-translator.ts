import agent from "@/app/i18n/messages/zh-cn/agent.json";
import auth from "@/app/i18n/messages/zh-cn/auth.json";
import charts from "@/app/i18n/messages/zh-cn/charts.json";
import common from "@/app/i18n/messages/zh-cn/common.json";
import dataset from "@/app/i18n/messages/zh-cn/dataset.json";
import errors from "@/app/i18n/messages/zh-cn/errors.json";
import evaluation from "@/app/i18n/messages/zh-cn/evaluation.json";
import layout from "@/app/i18n/messages/zh-cn/layout.json";
import leaderboard from "@/app/i18n/messages/zh-cn/leaderboard.json";
import network from "@/app/i18n/messages/zh-cn/network.json";
import publicMessages from "@/app/i18n/messages/zh-cn/public.json";
import submission from "@/app/i18n/messages/zh-cn/submission.json";
import validation from "@/app/i18n/messages/zh-cn/validation.json";

export type TranslateParams = Record<
  string,
  string | number | boolean | null | undefined
>;

export type AppTranslator = (key: string, params?: TranslateParams) => string;

const fallbackMessages: Record<string, unknown> = {
  agent,
  auth,
  charts,
  common,
  dataset,
  errors,
  evaluation,
  layout,
  leaderboard,
  network,
  public: publicMessages,
  submission,
  validation,
};

const readFallbackMessage = (key: string): string | null => {
  const value = key.split(".").reduce<unknown>((current, segment) => {
    if (!current || typeof current !== "object" || Array.isArray(current)) {
      return undefined;
    }

    return (current as Record<string, unknown>)[segment];
  }, fallbackMessages);

  return typeof value === "string" ? value : null;
};

const applyParams = (message: string, params?: TranslateParams): string =>
  params
    ? Object.entries(params).reduce(
        (current, [name, value]) =>
          current.replaceAll(`{${name}}`, String(value ?? "")),
        message,
      )
    : message;

let runtimeTranslator: AppTranslator = (key, params) =>
  applyParams(readFallbackMessage(key) ?? key, params);

export const setRuntimeTranslator = (translator: AppTranslator) => {
  runtimeTranslator = translator;
};

export const translateRuntimeMessage: AppTranslator = (key, params) =>
  runtimeTranslator(key, params);
