export interface HomeSectionScrollMetrics {
  currentScrollY: number;
  targetTop: number;
  viewportHeight: number;
  documentHeight: number;
  navHeight: number;
}

const SECTION_READING_TOP_RATIO = 0.25;
const MIN_SECTION_TOP_GAP = 16;

const finiteOrZero = (value: number): number =>
  Number.isFinite(value) ? value : 0;

const clamp = (value: number, min: number, max: number): number =>
  Math.min(Math.max(value, min), max);

export const resolveHomeSectionScrollTop = (
  metrics: HomeSectionScrollMetrics,
): number => {
  const currentScrollY = finiteOrZero(metrics.currentScrollY);
  const targetTop = finiteOrZero(metrics.targetTop);
  const viewportHeight = Math.max(0, finiteOrZero(metrics.viewportHeight));
  const documentHeight = Math.max(
    viewportHeight,
    finiteOrZero(metrics.documentHeight),
  );
  const navHeight = Math.max(0, finiteOrZero(metrics.navHeight));
  const maxScrollTop = Math.max(0, documentHeight - viewportHeight);
  const readableViewportHeight = Math.max(0, viewportHeight - navHeight);
  const preferredTopOffset =
    navHeight +
    Math.max(
      MIN_SECTION_TOP_GAP,
      Math.round(readableViewportHeight * SECTION_READING_TOP_RATIO),
    );

  return clamp(
    Math.round(currentScrollY + targetTop - preferredTopOffset),
    0,
    maxScrollTop,
  );
};
