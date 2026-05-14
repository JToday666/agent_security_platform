import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const currentDir = dirname(fileURLToPath(import.meta.url));
const readUiSelectSource = () =>
  readFileSync(resolve(currentDir, "UiSelect.vue"), "utf8");

describe("UiSelect accessibility interactions", () => {
  it("declares a controlled listbox relationship with active-descendant focus", () => {
    const source = readUiSelectSource();

    expect(source).toContain('aria-haspopup="listbox"');
    expect(source).toContain(":aria-controls=");
    expect(source).toContain('role="listbox"');
    expect(source).toContain('tabindex="-1"');
    expect(source).toContain(":aria-activedescendant=");
    expect(source).toContain('role="option"');
    expect(source).toContain(':id="optionIds[index]"');
  });

  it("handles the expected custom listbox keyboard model", () => {
    const source = readUiSelectSource();

    expect(source).toContain('@keydown="handleTriggerKeydown"');
    expect(source).toContain('@keydown="handleListboxKeydown"');
    expect(source).toContain('"ArrowDown"');
    expect(source).toContain('"ArrowUp"');
    expect(source).toContain('"Home"');
    expect(source).toContain('"End"');
    expect(source).toContain('"Enter"');
    expect(source).toContain('" "');
    expect(source).toContain('"Escape"');
    expect(source).toContain('"Tab"');
    expect(source).toContain("TYPEAHEAD_TIMEOUT_MS = 500");
  });

  it("keeps navigation and selection separate", () => {
    const source = readUiSelectSource();

    expect(source).toContain("moveActiveOption");
    expect(source).toContain("selectActiveOption");
    expect(source).toContain("if (!props.options.length)");
    expect(source).toContain("triggerRef.value?.focus()");
  });
});
