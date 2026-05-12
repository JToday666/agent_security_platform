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

const flattenStringEntries = (
  value: unknown,
  prefix = "",
  output: Array<{ key: string; value: string }> = [],
) => {
  if (typeof value === "string") {
    output.push({ key: prefix, value });
    return output;
  }

  if (value && typeof value === "object" && !Array.isArray(value)) {
    Object.entries(value as JsonRecord).forEach(([key, child]) => {
      flattenStringEntries(child, prefix ? `${prefix}.${key}` : key, output);
    });
  }

  return output;
};

const extractStringPlaceholders = (value: string): string[] =>
  Array.from(value.matchAll(/\{([A-Za-z0-9_]+)\}/g))
    .map((match) => match[1] ?? "")
    .sort();

const extractPlaceholdersByKey = (
  value: unknown,
  prefix = "",
  output = new Map<string, string[]>(),
) => {
  if (typeof value === "string") {
    output.set(prefix, extractStringPlaceholders(value));
    return output;
  }

  if (value && typeof value === "object" && !Array.isArray(value)) {
    Object.entries(value as JsonRecord).forEach(([key, child]) =>
      extractPlaceholdersByKey(child, prefix ? `${prefix}.${key}` : key, output),
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
      const schemaPlaceholdersByKey = extractPlaceholdersByKey(schema);

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

          const candidatePlaceholdersByKey = extractPlaceholdersByKey(candidate);
          schemaKeys.forEach((key) => {
            expect(
              candidatePlaceholdersByKey.get(key) ?? [],
              `${locale}/${domain}.${key} placeholders`,
            ).toEqual(schemaPlaceholdersByKey.get(key) ?? []);
          });
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

  it("keeps identical zh-CN source strings translated consistently", () => {
    const schemaLocale = "zh-CN";
    const sourceByKey = new Map<string, string>();

    MESSAGE_DOMAINS.forEach((domain) => {
      flattenStringEntries(readDomainMessages(schemaLocale, domain)).forEach(
        (entry) => sourceByKey.set(`${domain}.${entry.key}`, entry.value),
      );
    });

    SUPPORTED_LOCALES.filter((locale) => locale !== schemaLocale).forEach(
      (locale) => {
        const translatedBySource = new Map<string, string>();

        MESSAGE_DOMAINS.forEach((domain) => {
          flattenStringEntries(readDomainMessages(locale, domain)).forEach(
            (entry) => {
              const source = sourceByKey.get(`${domain}.${entry.key}`);
              if (!source) {
                return;
              }

              const previous = translatedBySource.get(source);
              expect(
                previous === undefined || previous === entry.value,
                `${locale}: "${source}" translated as both "${previous}" and "${entry.value}"`,
              ).toBe(true);
              translatedBySource.set(source, entry.value);
            },
          );
        });
      },
    );
  });

  it("keeps locked professional terminology consistent", () => {
    const forbiddenEnglishTerms = [
      /evaluation item/i,
      /test item/i,
      /risk area/i,
      /risk category/i,
    ];
    const forbiddenJapaneseTerms = [/リスクエリア/, /リスクカテゴリ/];

    MESSAGE_DOMAINS.forEach((domain) => {
      const zhEntries = flattenStringEntries(readDomainMessages("zh-CN", domain));
      const enEntries = flattenStringEntries(readDomainMessages("en-US", domain));
      const jaEntries = flattenStringEntries(readDomainMessages("ja-JP", domain));

      enEntries.forEach((entry) => {
        forbiddenEnglishTerms.forEach((term) => {
          expect(entry.value, `en-US/${domain}.${entry.key}`).not.toMatch(term);
        });
      });

      jaEntries.forEach((entry) => {
        forbiddenJapaneseTerms.forEach((term) => {
          expect(entry.value, `ja-JP/${domain}.${entry.key}`).not.toMatch(term);
        });
      });

      zhEntries.forEach((entry, index) => {
        if (entry.value.includes("评测项")) {
          expect(enEntries[index]?.value, `en-US/${domain}.${entry.key}`).toMatch(
            /benchmark item/i,
          );
        }

        if (entry.value.includes("风险域")) {
          expect(enEntries[index]?.value, `en-US/${domain}.${entry.key}`).toMatch(
            /risk domain/i,
          );
          expect(jaEntries[index]?.value, `ja-JP/${domain}.${entry.key}`).toContain(
            "リスク領域",
          );
        }
      });
    });
  });
});
