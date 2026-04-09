import { onBeforeUnmount, onMounted, ref } from "vue";

interface UseTypewriterTextOptions {
  sessionKey: string;
  primaryText: string;
  secondaryText: string;
  primaryMsPerChar?: number;
  secondaryMsPerChar?: number;
  secondaryDelayMs?: number;
}

const SESSION_DONE_VALUE = "done";

export const useTypewriterText = ({
  sessionKey,
  primaryText,
  secondaryText,
  primaryMsPerChar = 96,
  secondaryMsPerChar = 60,
  secondaryDelayMs = 180,
}: UseTypewriterTextOptions) => {
  const typedPrimaryText = ref("");
  const typedSecondaryText = ref("");
  const isPrimaryTyping = ref(false);
  const isSecondaryTyping = ref(false);

  let animationFrameId: number | null = null;
  let animationStage: "primary" | "pause" | "secondary" | "done" = "done";
  let stageStartedAt = 0;
  let secondaryStartsAt = 0;

  const getTypedLength = (
    text: string,
    msPerChar: number,
    timestamp: number,
  ): number =>
    Math.min(
      text.length,
      Math.max(1, Math.floor((timestamp - stageStartedAt) / msPerChar) + 1),
    );

  const markCompleted = () => {
    typedPrimaryText.value = primaryText;
    typedSecondaryText.value = secondaryText;
    isPrimaryTyping.value = false;
    isSecondaryTyping.value = false;
    animationStage = "done";

    try {
      window.sessionStorage.setItem(sessionKey, SESSION_DONE_VALUE);
    } catch {
      // Ignore storage failures and keep the visual behavior intact.
    }
  };

  const stopAnimation = () => {
    if (animationFrameId !== null) {
      window.cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  };

  const tick = (timestamp: number) => {
    if (animationStage === "done") {
      stopAnimation();
      return;
    }

    if (animationStage === "primary") {
      if (stageStartedAt === 0) {
        stageStartedAt = timestamp;
      }

      const nextLength = getTypedLength(
        primaryText,
        primaryMsPerChar,
        timestamp,
      );
      typedPrimaryText.value = primaryText.slice(0, nextLength);

      if (nextLength >= primaryText.length) {
        isPrimaryTyping.value = false;
        animationStage = "pause";
        secondaryStartsAt = timestamp + secondaryDelayMs;
      }
    } else if (animationStage === "pause") {
      if (timestamp >= secondaryStartsAt) {
        animationStage = "secondary";
        stageStartedAt = timestamp;
        isSecondaryTyping.value = true;
      }
    } else if (animationStage === "secondary") {
      const nextLength = getTypedLength(
        secondaryText,
        secondaryMsPerChar,
        timestamp,
      );
      typedSecondaryText.value = secondaryText.slice(0, nextLength);

      if (nextLength >= secondaryText.length) {
        markCompleted();
      }
    }

    animationFrameId = window.requestAnimationFrame(tick);
  };

  onMounted(() => {
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    try {
      if (
        prefersReducedMotion ||
        window.sessionStorage.getItem(sessionKey) === SESSION_DONE_VALUE
      ) {
        markCompleted();
        return;
      }
    } catch {
      if (prefersReducedMotion) {
        markCompleted();
        return;
      }
    }

    typedPrimaryText.value = "";
    typedSecondaryText.value = "";
    isPrimaryTyping.value = true;
    isSecondaryTyping.value = false;
    animationStage = "primary";
    stageStartedAt = 0;
    secondaryStartsAt = 0;
    animationFrameId = window.requestAnimationFrame(tick);
  });

  onBeforeUnmount(() => {
    stopAnimation();
  });

  return {
    typedPrimaryText,
    typedSecondaryText,
    isPrimaryTyping,
    isSecondaryTyping,
  };
};
