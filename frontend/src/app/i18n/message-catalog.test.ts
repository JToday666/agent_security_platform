import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

type MessageTree = Record<string, unknown>;

const messagesDir = join(process.cwd(), "src", "app", "i18n", "messages");
const placeholderPattern = /\{([A-Za-z0-9_]+)\}/g;
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
          expect(placeholders(candidate[key])).toEqual(placeholders(source[key]));
        }
      }
    }
  });

  it("uses standard French and Spanish orthography", () => {
    const checkLocale = (locale: string, pattern: RegExp) => {
      const hits = readdirSync(join(messagesDir, locale)).flatMap((domain) =>
        Object.entries(readDomain(locale, domain))
          .filter(([, message]) => pattern.test(message))
          .map(([key, message]) => `${domain}:${key}=${message}`),
      );

      expect(hits).toEqual([]);
    };

    checkLocale("fr-fr", frenchAsciiAccentWords);
    checkLocale("es-es", spanishAsciiAccentWords);
  });

  it("preserves do-not-translate terms in Japanese", () => {
    const text = readdirSync(join(messagesDir, "ja-jp"))
      .map((domain) => Object.values(readDomain("ja-jp", domain)).join("\n"))
      .join("\n");

    expect(text).toContain("Agent");
    expect(text).not.toContain("エージェント");
  });
});
