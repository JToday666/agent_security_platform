import { onBeforeUnmount } from "vue";

export const usePolling = (
  loader: () => Promise<void>,
  shouldPoll: () => boolean,
  intervalMs = 10 * 60 * 1000,
) => {
  let timerId: number | null = null;

  const stop = () => {
    if (timerId !== null) {
      window.clearInterval(timerId);
      timerId = null;
    }
  };

  const start = () => {
    stop();
    if (!shouldPoll()) return;

    timerId = window.setInterval(() => {
      void loader();
    }, intervalMs);
  };

  onBeforeUnmount(() => {
    stop();
  });

  return { start, stop };
};
