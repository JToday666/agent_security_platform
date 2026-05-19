import { createI18n } from "vue-i18n";
import type { Router, RouteLocationNormalizedLoaded } from "vue-router";
import { setApiLocale } from "@/shared/api/http-client";
import { STORAGE_KEYS } from "@/shared/constants/storage-keys";
import { useLocaleStore } from "@/app/i18n/localeStore";
import { setRuntimeTranslator } from "@/app/i18n/runtime-translator";

export const SUPPORTED_LOCALES = [
  "zh-CN",
  "en-US",
  "fr-FR",
  "es-ES",
  "ja-JP",
] as const;

export const DEFAULT_LOCALE = "zh-CN";

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export const MESSAGE_DOMAINS = [
  "common",
  "layout",
  "auth",
  "public",
  "dataset",
  "agent",
  "submission",
  "evaluation",
  "leaderboard",
  "charts",
  "errors",
  "validation",
  "network",
] as const;

export type MessageDomain = (typeof MESSAGE_DOMAINS)[number];

type MessageTree = Record<string, unknown>;

interface PreferredLocaleOptions {
  explicitLocale?: string | null;
  storedLocale?: string | null;
  browserLocales?: readonly string[] | null;
}

interface ResolvedLocalePath {
  locale: SupportedLocale;
  path: string;
  redirect: boolean;
}

const localeAliasMap: Record<string, SupportedLocale> = {
  zh: "zh-CN",
  "zh-cn": "zh-CN",
  "zh-hans": "zh-CN",
  "zh-hans-cn": "zh-CN",
  en: "en-US",
  "en-us": "en-US",
  "en-gb": "en-US",
  fr: "fr-FR",
  "fr-fr": "fr-FR",
  "fr-ca": "fr-FR",
  es: "es-ES",
  "es-es": "es-ES",
  "es-mx": "es-ES",
  ja: "ja-JP",
  "ja-jp": "ja-JP",
};

const localeSegmentPattern = /^[a-z]{2}(?:-[a-z0-9]+)?$/i;
const loadedLocales = new Set<SupportedLocale>();
const loadingLocales = new Map<SupportedLocale, Promise<void>>();
const messageModules = import.meta.glob("./messages/*/*.json");
let activateLocaleSeq = 0;

export const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages: {},
});

setRuntimeTranslator((key, params) => String(i18n.global.t(key, params ?? {})));

export const toLocaleDirectoryName = (locale: SupportedLocale): string =>
  locale.toLowerCase();

export const normalizeLocale = (locale?: string | null): SupportedLocale => {
  if (!locale) {
    return DEFAULT_LOCALE;
  }

  const normalized = locale.trim().replace(/_/g, "-").toLowerCase();
  return localeAliasMap[normalized] ?? DEFAULT_LOCALE;
};

export const isCanonicalSupportedLocale = (
  locale?: string | null,
): locale is SupportedLocale =>
  SUPPORTED_LOCALES.includes(locale as SupportedLocale);

export const isLocaleLikeSegment = (segment?: string | null): boolean =>
  Boolean(segment && localeSegmentPattern.test(segment));

export const resolvePreferredLocale = (
  options: PreferredLocaleOptions = {},
): SupportedLocale => {
  const candidates = [
    options.explicitLocale,
    options.storedLocale,
    ...(options.browserLocales ?? []),
  ];

  const supportedCandidate = candidates.find((candidate) => {
    if (!candidate) {
      return false;
    }
    const normalized = normalizeLocale(candidate);
    return (
      normalized !== DEFAULT_LOCALE ||
      candidate.trim().toLowerCase().startsWith("zh")
    );
  });

  return supportedCandidate
    ? normalizeLocale(supportedCandidate)
    : DEFAULT_LOCALE;
};

export const readStoredLocale = (): string | null => {
  if (typeof localStorage === "undefined") {
    return null;
  }

  return localStorage.getItem(STORAGE_KEYS.i18n.displayLocale);
};

export const readBrowserLocales = (): string[] => {
  if (typeof navigator === "undefined") {
    return [];
  }

  return Array.from(
    navigator.languages?.length ? navigator.languages : [navigator.language],
  ).filter(Boolean);
};

export const resolveRuntimePreferredLocale = (): SupportedLocale =>
  resolvePreferredLocale({
    storedLocale: readStoredLocale(),
    browserLocales: readBrowserLocales(),
  });

const splitFullPath = (fullPath: string) => {
  const hashIndex = fullPath.indexOf("#");
  const beforeHash = hashIndex >= 0 ? fullPath.slice(0, hashIndex) : fullPath;
  const hash = hashIndex >= 0 ? fullPath.slice(hashIndex) : "";
  const queryIndex = beforeHash.indexOf("?");
  const pathname =
    queryIndex >= 0 ? beforeHash.slice(0, queryIndex) : beforeHash;
  const query = queryIndex >= 0 ? beforeHash.slice(queryIndex) : "";

  return {
    pathname: pathname || "/",
    suffix: `${query}${hash}`,
  };
};

const joinLocalePath = (
  locale: SupportedLocale,
  pathWithoutLocale: string,
  suffix: string,
) => {
  const normalizedPath =
    pathWithoutLocale === "/" || pathWithoutLocale === ""
      ? "/"
      : pathWithoutLocale.startsWith("/")
        ? pathWithoutLocale
        : `/${pathWithoutLocale}`;

  return `/${locale}${normalizedPath}${suffix}`;
};

export const resolveLocalePath = (
  fullPath: string,
  preferredLocale: SupportedLocale = resolveRuntimePreferredLocale(),
): ResolvedLocalePath => {
  const preferred = normalizeLocale(preferredLocale);
  const { pathname, suffix } = splitFullPath(fullPath || "/");
  const normalizedPathname = pathname.startsWith("/")
    ? pathname
    : `/${pathname}`;
  const segments = normalizedPathname.split("/").filter(Boolean);
  const firstSegment = segments[0];

  if (!firstSegment) {
    return {
      locale: preferred,
      path: `/${preferred}/${suffix}`,
      redirect: true,
    };
  }

  const normalizedLocale = normalizeLocale(firstSegment);
  const remainingPath = `/${segments.slice(1).join("/")}`;

  if (isCanonicalSupportedLocale(firstSegment)) {
    return {
      locale: firstSegment,
      path: `${normalizedPathname}${suffix}`,
      redirect: false,
    };
  }

  if (isLocaleLikeSegment(firstSegment)) {
    if (
      normalizedLocale !== DEFAULT_LOCALE ||
      firstSegment.toLowerCase().startsWith("zh")
    ) {
      return {
        locale: normalizedLocale,
        path: joinLocalePath(normalizedLocale, remainingPath, suffix),
        redirect: true,
      };
    }

    return {
      locale: DEFAULT_LOCALE,
      path: joinLocalePath(DEFAULT_LOCALE, remainingPath, suffix),
      redirect: true,
    };
  }

  return {
    locale: preferred,
    path: joinLocalePath(preferred, normalizedPathname, suffix),
    redirect: true,
  };
};

const readMessageDomain = async (
  locale: SupportedLocale,
  domain: MessageDomain,
): Promise<MessageTree> => {
  const modulePath = `./messages/${toLocaleDirectoryName(locale)}/${domain}.json`;
  const loader = messageModules[modulePath];

  if (!loader) {
    return {};
  }

  const module = (await loader()) as { default?: MessageTree };
  return module.default ?? {};
};

export const loadLocaleMessages = async (
  locale: SupportedLocale,
): Promise<void> => {
  if (loadedLocales.has(locale)) {
    return;
  }

  const loadingLocale = loadingLocales.get(locale);
  if (loadingLocale) {
    return loadingLocale;
  }

  const loadLocale = Promise.all(
    MESSAGE_DOMAINS.map(async (domain) => [
      domain,
      await readMessageDomain(locale, domain),
    ]),
  )
    .then((domains) => {
      i18n.global.setLocaleMessage(locale, Object.fromEntries(domains));
      loadedLocales.add(locale);
    })
    .finally(() => {
      loadingLocales.delete(locale);
    });

  loadingLocales.set(locale, loadLocale);
  return loadLocale;
};

export const getCurrentDisplayLocale = (): SupportedLocale =>
  normalizeLocale(i18n.global.locale.value);

export const activateLocale = async (
  locale: string | null | undefined,
): Promise<SupportedLocale> => {
  const normalizedLocale = normalizeLocale(locale);
  const currentSeq = ++activateLocaleSeq;
  await Promise.all([
    loadLocaleMessages(normalizedLocale),
    ...(normalizedLocale === DEFAULT_LOCALE
      ? []
      : [loadLocaleMessages(DEFAULT_LOCALE)]),
  ]);

  if (currentSeq !== activateLocaleSeq) {
    return getCurrentDisplayLocale();
  }

  i18n.global.locale.value = normalizedLocale;
  setApiLocale(normalizedLocale);

  if (typeof document !== "undefined") {
    document.documentElement.lang = normalizedLocale;
  }

  if (typeof localStorage !== "undefined") {
    localStorage.setItem(STORAGE_KEYS.i18n.displayLocale, normalizedLocale);
  }

  const localeStore = useLocaleStore();
  localeStore.setLocale(normalizedLocale);
  localeStore.markLocaleLoaded(normalizedLocale);

  return normalizedLocale;
};

export const switchLocale = async (
  router: Router,
  route: RouteLocationNormalizedLoaded,
  locale: string,
) => {
  const targetLocale = normalizeLocale(locale);
  const { pathname, suffix } = splitFullPath(route.fullPath);
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length && isLocaleLikeSegment(segments[0])) {
    segments[0] = targetLocale;
  } else {
    segments.unshift(targetLocale);
  }

  return router.push(`/${segments.join("/")}${suffix}`);
};

export default i18n;
