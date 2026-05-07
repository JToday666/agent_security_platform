<template>
  <figure
    class="agent-code-preview"
    :class="[
      `agent-code-preview--${language}`,
      { 'agent-code-preview--fill': fillHeight },
    ]"
    :style="{ '--agent-code-preview-max-height': maxHeight }"
  >
    <pre class="agent-code-preview__surface"><code><span
      v-for="(segment, index) in highlightedSegments"
      :key="`${index}-${segment.kind}`"
      :class="`agent-code-preview__token agent-code-preview__token--${segment.kind}`"
    >{{ segment.text }}</span></code></pre>
  </figure>
</template>

<script setup lang="ts">
import { computed } from "vue";

type CodeLanguage = "curl" | "python" | "json";
type TokenKind =
  | "base"
  | "command"
  | "flag"
  | "url"
  | "method"
  | "string"
  | "keyword"
  | "number"
  | "boolean"
  | "null"
  | "key"
  | "punctuation"
  | "comment"
  | "escape";

interface CodeSegment {
  text: string;
  kind: TokenKind;
}

const props = withDefaults(
  defineProps<{
    code: string;
    language: CodeLanguage;
    maxHeight?: string;
    fillHeight?: boolean;
  }>(),
  {
    maxHeight: "620px",
    fillHeight: false,
  },
);

const appendPlainText = (
  segments: CodeSegment[],
  source: string,
  start: number,
  end: number,
) => {
  if (end > start) {
    segments.push({ text: source.slice(start, end), kind: "base" });
  }
};

const tokenizeWithPattern = (
  source: string,
  pattern: RegExp,
  resolveKind: (token: string, match: RegExpMatchArray) => TokenKind,
): CodeSegment[] => {
  const segments: CodeSegment[] = [];
  let lastIndex = 0;

  for (const match of source.matchAll(pattern)) {
    const token = match[0];
    const index = match.index ?? 0;
    appendPlainText(segments, source, lastIndex, index);
    segments.push({ text: token, kind: resolveKind(token, match) });
    lastIndex = index + token.length;
  }

  appendPlainText(segments, source, lastIndex, source.length);
  return segments;
};

const tokenizeCurl = (source: string): CodeSegment[] =>
  tokenizeWithPattern(
    source,
    /curl|--[a-z0-9-]+|https?:\/\/[^\s'"\\]+|\\|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|\b(?:GET|POST|PUT|PATCH|DELETE)\b/gi,
    (token) => {
      if (token === "\\") {
        return "escape";
      }
      if (/^curl$/i.test(token)) {
        return "command";
      }
      if (token.startsWith("--")) {
        return "flag";
      }
      if (/^https?:\/\//i.test(token)) {
        return "url";
      }
      if (/^(GET|POST|PUT|PATCH|DELETE)$/i.test(token)) {
        return "method";
      }
      return "string";
    },
  );

const tokenizePython = (source: string): CodeSegment[] =>
  tokenizeWithPattern(
    source,
    /#.*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:as|def|elif|else|except|False|for|from|if|import|in|None|return|True|try|with)\b|\b\d+(?:\.\d+)?\b/g,
    (token) => {
      if (token.startsWith("#")) {
        return "comment";
      }
      if (token.startsWith('"') || token.startsWith("'")) {
        return "string";
      }
      if (/^\d/.test(token)) {
        return "number";
      }
      if (token === "True" || token === "False") {
        return "boolean";
      }
      if (token === "None") {
        return "null";
      }
      return "keyword";
    },
  );

const tokenizeJson = (source: string): CodeSegment[] =>
  tokenizeWithPattern(
    source,
    /"(?:\\.|[^"\\])*"(?=\s*:)|"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\b(?:true|false|null)\b|[{}[\],:]/g,
    (token, match) => {
      if (token.startsWith('"')) {
        const nextCharacter = source
          .slice((match.index ?? 0) + token.length)
          .trimStart()
          .charAt(0);
        return nextCharacter === ":" ? "key" : "string";
      }
      if (token === "true" || token === "false") {
        return "boolean";
      }
      if (token === "null") {
        return "null";
      }
      if (/^-?\d/.test(token)) {
        return "number";
      }
      return "punctuation";
    },
  );

const highlightedSegments = computed<CodeSegment[]>(() => {
  if (props.language === "curl") {
    return tokenizeCurl(props.code);
  }
  if (props.language === "python") {
    return tokenizePython(props.code);
  }
  return tokenizeJson(props.code);
});
</script>

<style scoped lang="scss">
.agent-code-preview {
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin: 0;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: var(--radius-card-sm);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.92)),
    #f8fafc;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.86),
    0 18px 36px rgba(15, 23, 42, 0.08);
  overflow: hidden;
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.agent-code-preview--fill {
  height: 100%;
  min-height: 0;
}

.agent-code-preview:hover,
.agent-code-preview:focus-within {
  border-color: rgba(99, 102, 241, 0.34);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.88),
    0 22px 42px rgba(79, 70, 229, 0.12);
}

.agent-code-preview__surface {
  flex: 0 1 auto;
  max-height: var(--agent-code-preview-max-height);
  overflow: auto;
  margin: 0;
  padding: 1.05rem 1.1rem;
  color: #00357a;
  font-family:
    "SFMono-Regular",
    "Cascadia Code",
    "Fira Code",
    Consolas,
    "Liberation Mono",
    monospace;
  font-size: 0.86rem;
  font-weight: 500;
  line-height: 1.78;
  white-space: pre;
  tab-size: 2;
}

.agent-code-preview--fill .agent-code-preview__surface {
  flex: 1 1 auto;
  min-height: 0;
  max-height: none;
}

.agent-code-preview__surface::selection,
.agent-code-preview__surface *::selection {
  background: rgba(59, 130, 246, 0.2);
  color: #001f4d;
}

.agent-code-preview__surface::-webkit-scrollbar {
  width: 0.72rem;
  height: 0.72rem;
}

.agent-code-preview__surface::-webkit-scrollbar-thumb {
  border: 0.18rem solid rgba(248, 250, 252, 0.92);
  border-radius: var(--radius-pill);
  background: rgba(99, 102, 241, 0.28);
}

.agent-code-preview__surface::-webkit-scrollbar-track {
  background: transparent;
}

.agent-code-preview__token--command,
.agent-code-preview__token--method {
  color: #b45309;
  font-weight: 800;
}

.agent-code-preview__token--flag,
.agent-code-preview__token--keyword {
  color: #075fb8;
  font-weight: 700;
}

.agent-code-preview__token--url {
  color: #0f63c7;
  text-decoration: underline;
  text-decoration-color: rgba(15, 99, 199, 0.24);
  text-underline-offset: 0.16em;
}

.agent-code-preview__token--string {
  color: #003b8f;
}

.agent-code-preview__token--key {
  color: #00357a;
  font-weight: 800;
}

.agent-code-preview__token--number {
  color: #7c2d12;
}

.agent-code-preview__token--boolean,
.agent-code-preview__token--null {
  color: #7e22ce;
  font-weight: 700;
}

.agent-code-preview__token--punctuation,
.agent-code-preview__token--escape {
  color: #dc2626;
  font-weight: 700;
}

.agent-code-preview__token--comment {
  color: #64748b;
  font-style: italic;
}

@media (prefers-reduced-motion: reduce) {
  .agent-code-preview {
    transition: none;
  }
}
</style>
