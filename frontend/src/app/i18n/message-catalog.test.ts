import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { extname, join, relative } from "node:path";
import {
  MESSAGE_DOMAINS,
  normalizeLocale,
  resolveLocalePath,
  resolvePreferredLocale,
} from ".";

type MessageTree = Record<string, unknown>;

const messagesDir = join(process.cwd(), "src", "app", "i18n", "messages");
const sourceDir = join(process.cwd(), "src");
const aegisExpansion = "Agents Evaluation and Guardrail Inspection System";
const placeholderPattern = /\{([A-Za-z0-9_]+)\}/g;
const cjkPattern = /[\u3400-\u9fff]/;
const cjkStringLinePattern =
  /(["'`])(?:\\.|(?!\1).)*[\u3400-\u9fff](?:\\.|(?!\1).)*\1/g;
const publicMetaCopyPattern =
  /(?:mock|coming soon|wireframe|layout|implementation|developer|评审|设计|布局说明|开发|実装|レイアウト|diseño|maqueta|mise en page|développement)/i;
const frenchAsciiAccentWords =
  /\b(?:etre|etes|ete|acces|succes|verification|verifies|Reessayez|tache|resultat|execution|donnees|difficulte|deja|enregistre|parametres|depasser|depassent|criteres|Selectionnez|evaluation|echantillon|echantillons|televerser|echoue|echeance|apres|creee|demarrer|arret|generera|methode|modifie|refuse|connecte|expire|retourne)\b/i;
const spanishAsciiAccentWords =
  /\b(?:vacio|vacios|devolvio|Intentalo|envian|despues|ejecucion|contrasena|sesion|codigo|version|evaluacion|parametros|aparecera|clasificacion|publica|Asegurate|descripcion|informacion|accion|metodo|puntuacion|recalculo|anonimo|envio|Asincrono|valido|terminara|generara|mas|tambien|reanudala|pausara)\b/i;

const flattenMessages = (
  value: unknown,
  prefix = "",
): Record<string, string> => {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return Object.entries(value as MessageTree).reduce<Record<string, string>>(
      (acc, [key, nestedValue]) => ({
        ...acc,
        ...flattenMessages(nestedValue, prefix ? `${prefix}.${key}` : key),
      }),
      {},
    );
  }

  return typeof value === "string" ? { [prefix]: value } : {};
};

const readDomain = (locale: string, domain: string): Record<string, string> => {
  const filePath = join(messagesDir, locale, domain);
  return flattenMessages(JSON.parse(readFileSync(filePath, "utf-8")));
};

const placeholders = (message: string): string[] =>
  Array.from(message.matchAll(placeholderPattern), (match) => match[1]).sort();

const listSourceFiles = (dir: string): string[] =>
  readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    return entry.isDirectory() ? listSourceFiles(path) : [path];
  });

const stripComments = (source: string): string =>
  source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|\s)\/\/.*$/gm, "");

const normalizedSourcePath = (filePath: string): string =>
  relative(sourceDir, filePath).replace(/\\/g, "/");

const shouldSkipHardcodedChineseFile = (filePath: string): boolean => {
  const normalizedPath = normalizedSourcePath(filePath);
  return (
    normalizedPath === "app/i18n/message-catalog.test.ts" ||
    normalizedPath.endsWith(".test.ts") ||
    normalizedPath.includes("/api/internal/") ||
    normalizedPath.includes("/fixtures/") ||
    normalizedPath.includes("/mock/")
  );
};

const isAllowedHardcodedChinese = (
  filePath: string,
  match: string,
): boolean => {
  const normalizedPath = normalizedSourcePath(filePath);
  if (shouldSkipHardcodedChineseFile(filePath)) {
    return true;
  }
  if (normalizedPath === "app/shell/language-switcher.ts") {
    return match.includes("汉语") || match.includes("日本語");
  }
  if (normalizedPath === "modules/dataset/model/dataset-taxonomy.ts") {
    return true;
  }
  if (normalizedPath === "modules/dataset/api/dataset-api.ts") {
    return [
      "目录加载失败，请稍后重试。",
      "详情加载失败，请稍后重试。",
      "未找到对应评测项。",
    ].some((allowed) => match.includes(allowed));
  }
  return false;
};

describe("frontend i18n message catalogs", () => {
  it("keeps keys and placeholders aligned across locales", () => {
    const locales = readdirSync(messagesDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);
    const domains = readdirSync(join(messagesDir, "zh-cn"));

    for (const domain of domains) {
      const source = readDomain("zh-cn", domain);
      const sourceKeys = Object.keys(source).sort();

      for (const locale of locales) {
        const candidate = readDomain(locale, domain);
        expect(Object.keys(candidate).sort()).toEqual(sourceKeys);
        for (const key of sourceKeys) {
          expect(placeholders(candidate[key])).toEqual(
            placeholders(source[key]),
          );
        }
      }
    }
  });

  it("keeps intentionally empty domains consistent across locales", () => {
    const locales = readdirSync(messagesDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);
    const sourceEmptyDomains = MESSAGE_DOMAINS.filter(
      (domain) =>
        Object.keys(readDomain("zh-cn", `${domain}.json`)).length === 0,
    );

    expect(sourceEmptyDomains).toEqual(["charts", "errors", "validation"]);

    for (const locale of locales) {
      const emptyDomains = MESSAGE_DOMAINS.filter(
        (domain) =>
          Object.keys(readDomain(locale, `${domain}.json`)).length === 0,
      );
      expect(emptyDomains).toEqual(sourceEmptyDomains);
    }
  });

  it("uses standard French and Spanish orthography", () => {
    const stripProtectedTerms = (message: string): string =>
      message.replaceAll(aegisExpansion, "");

    const checkLocale = (locale: string, pattern: RegExp) => {
      const hits = readdirSync(join(messagesDir, locale)).flatMap((domain) =>
        Object.entries(readDomain(locale, domain))
          .filter(([, message]) => pattern.test(stripProtectedTerms(message)))
          .map(([key, message]) => `${domain}:${key}=${message}`),
      );

      expect(hits).toEqual([]);
    };

    checkLocale("fr-fr", frenchAsciiAccentWords);
    checkLocale("es-es", spanishAsciiAccentWords);
  });

  it("keeps the AEGIS expansion untranslated on the public home page", () => {
    const locales = readdirSync(messagesDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);

    for (const locale of locales) {
      const publicMessages = readDomain(locale, "public.json");

      expect(publicMessages["home.hero.descriptionPrimary"]).toBe(
        aegisExpansion,
      );
      expect(publicMessages["home.sections.aegis.expansion"]).toBe(
        aegisExpansion,
      );
    }
  });

  it("keeps public home copy free of developer-facing meta language", () => {
    const locales = readdirSync(messagesDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);

    const hits = locales.flatMap((locale) =>
      Object.entries(readDomain(locale, "public.json"))
        .filter(([, message]) => publicMetaCopyPattern.test(message))
        .map(([key, message]) => `${locale}:${key}=${message}`),
    );

    expect(hits).toEqual([]);
  });

  it("preserves do-not-translate terms in Japanese", () => {
    const text = readdirSync(join(messagesDir, "ja-jp"))
      .map((domain) => Object.values(readDomain("ja-jp", domain)).join("\n"))
      .join("\n");

    expect(text).toContain("Agent");
    expect(text).not.toContain("エージェント");
  });

  it("keeps non-mock user-visible Chinese in message catalogs", () => {
    const sourceFiles = listSourceFiles(sourceDir).filter(
      (filePath) =>
        [".ts", ".vue"].includes(extname(filePath)) &&
        !shouldSkipHardcodedChineseFile(filePath),
    );
    const hits = sourceFiles.flatMap((filePath) => {
      const source = stripComments(readFileSync(filePath, "utf-8"));
      if (!cjkPattern.test(source)) {
        return [];
      }
      return source.split(/\r?\n/).flatMap((line) =>
        Array.from(line.matchAll(cjkStringLinePattern), (match) => match[0])
          .filter((match) => cjkPattern.test(match))
          .filter((match) => !isAllowedHardcodedChinese(filePath, match))
          .map((match) => `${normalizedSourcePath(filePath)}: ${match}`),
      );
    });

    expect(hits).toEqual([]);
  });
});

describe("frontend locale routing", () => {
  it("normalizes supported locale aliases consistently", () => {
    expect(normalizeLocale("fr-CA")).toBe("fr-FR");
    expect(normalizeLocale("es-MX")).toBe("es-ES");
    expect(normalizeLocale("ja")).toBe("ja-JP");
    expect(resolvePreferredLocale({ storedLocale: "fr-CA" })).toBe("fr-FR");
  });

  it("preserves query and hash while canonicalizing locale paths", () => {
    expect(resolveLocalePath("/fr/dataset?tab=all#top", "zh-CN")).toEqual({
      locale: "fr-FR",
      path: "/fr-FR/dataset?tab=all#top",
      redirect: true,
    });
    expect(resolveLocalePath("/de-DE/dataset?tab=all#top", "en-US")).toEqual({
      locale: "zh-CN",
      path: "/zh-CN/dataset?tab=all#top",
      redirect: true,
    });
    expect(resolveLocalePath("/dataset?tab=all#top", "en-US")).toEqual({
      locale: "en-US",
      path: "/en-US/dataset?tab=all#top",
      redirect: true,
    });
  });
});
