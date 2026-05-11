import { describe, expect, it } from "vitest";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import {
  MESSAGE_DOMAINS,
  SUPPORTED_LOCALES,
  toLocaleDirectoryName,
} from "@/app/i18n";

type JsonRecord = Record<string, unknown>;

const messagesRoot = join(process.cwd(), "src", "app", "i18n", "messages");

const readDomainMessages = (
  locale: (typeof SUPPORTED_LOCALES)[number],
  domain: (typeof MESSAGE_DOMAINS)[number],
) =>
  JSON.parse(
    readFileSync(
      join(messagesRoot, toLocaleDirectoryName(locale), `${domain}.json`),
      "utf8",
    ),
  ) as JsonRecord;

const flattenKeys = (
  value: unknown,
  prefix = "",
  output: string[] = [],
): string[] => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    if (prefix) {
      output.push(prefix);
    }
    return output;
  }

  Object.entries(value as JsonRecord).forEach(([key, child]) => {
    flattenKeys(child, prefix ? `${prefix}.${key}` : key, output);
  });

  return output;
};

const extractPlaceholders = (value: unknown, output = new Set<string>()) => {
  if (typeof value === "string") {
    const matches = value.matchAll(/\{([A-Za-z0-9_]+)\}/g);
    Array.from(matches).forEach((match) => output.add(match[1] ?? ""));
    return output;
  }

  if (value && typeof value === "object" && !Array.isArray(value)) {
    Object.values(value as JsonRecord).forEach((child) =>
      extractPlaceholders(child, output),
    );
  }

  return output;
};

describe("i18n message catalogs", () => {
  it("provides every configured message domain for every supported locale", () => {
    SUPPORTED_LOCALES.forEach((locale) => {
      const localeDirectory = join(messagesRoot, toLocaleDirectoryName(locale));
      expect(existsSync(localeDirectory), `${locale} directory`).toBe(true);

      const files = readdirSync(localeDirectory)
        .filter((fileName) => fileName.endsWith(".json"))
        .sort();

      expect(files).toEqual(
        MESSAGE_DOMAINS.map((domain) => `${domain}.json`).sort(),
      );
    });
  });

  it("keeps message keys and placeholders aligned with zh-CN", () => {
    const schemaLocale = "zh-CN";
    const schemaDirectory = join(
      messagesRoot,
      toLocaleDirectoryName(schemaLocale),
    );

    MESSAGE_DOMAINS.forEach((domain) => {
      const schema = JSON.parse(
        readFileSync(join(schemaDirectory, `${domain}.json`), "utf8"),
      ) as JsonRecord;
      const schemaKeys = flattenKeys(schema).sort();
      const schemaPlaceholders = Array.from(extractPlaceholders(schema)).sort();

      SUPPORTED_LOCALES.filter((locale) => locale !== schemaLocale).forEach(
        (locale) => {
          const candidate = JSON.parse(
            readFileSync(
              join(messagesRoot, toLocaleDirectoryName(locale), `${domain}.json`),
              "utf8",
            ),
          ) as JsonRecord;

          expect(flattenKeys(candidate).sort(), `${locale}/${domain}`).toEqual(
            schemaKeys,
          );
          expect(
            Array.from(extractPlaceholders(candidate)).sort(),
            `${locale}/${domain} placeholders`,
          ).toEqual(schemaPlaceholders);
        },
      );
    });
  });

  it("keeps the platform brand name in common messages only", () => {
    SUPPORTED_LOCALES.forEach((locale) => {
      const common = readDomainMessages(locale, "common");
      const publicMessages = readDomainMessages(locale, "public");

      const brandName = (common.brand as JsonRecord | undefined)?.name;
      const home = publicMessages.home as JsonRecord | undefined;
      const hero = home?.hero as JsonRecord | undefined;

      expect(typeof brandName, `${locale} common.brand.name`).toBe("string");
      expect(hero, `${locale} public.home.hero`).not.toHaveProperty("title");
    });
  });
});
