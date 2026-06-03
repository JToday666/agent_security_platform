export const LUCIDE_ICON_NAMES = [
  "alert-triangle",
  "archive",
  "arrow-down",
  "arrow-left",
  "arrow-right",
  "arrow-up",
  "arrow-up-down",
  "ban",
  "bot",
  "bot-message-square",
  "check",
  "chevron-down",
  "chevron-right",
  "chevron-up",
  "chevrons-up-down",
  "circle-check-big",
  "clipboard-list",
  "clock-3",
  "copy",
  "copy-plus",
  "database",
  "download",
  "eye",
  "file-bar-chart-2",
  "file-check-2",
  "file-clock",
  "file-minus",
  "file-plus-2",
  "file-search",
  "globe",
  "house",
  "key-round",
  "languages",
  "link",
  "list",
  "list-filter",
  "list-x",
  "loader-circle",
  "lock",
  "log-in",
  "log-out",
  "mail",
  "map-pin",
  "menu",
  "messages-square",
  "octagon-x",
  "package",
  "panel-left-close",
  "panel-left-open",
  "pause",
  "pause-circle",
  "phone",
  "play",
  "plug-zap",
  "plus",
  "refresh-cw",
  "rotate-ccw",
  "rotate-cw",
  "save",
  "search",
  "send",
  "shield-check",
  "shield-question",
  "sliders-horizontal",
  "square",
  "square-pen",
  "trash-2",
  "triangle-alert",
  "trophy",
  "upload",
  "user",
  "waypoints",
  "workflow",
  "x",
  "x-circle",
] as const;

export type LucideIconName = (typeof LUCIDE_ICON_NAMES)[number];

export const BRAND_ICON_NAMES = ["github", "x"] as const;

export type BrandIconName = (typeof BRAND_ICON_NAMES)[number];

export const APP_ICON_FALLBACK = "shield-question" satisfies LucideIconName;

type AppIconAliasTarget = LucideIconName | `brand:${BrandIconName}`;

export const APP_ICON_ALIASES = {
  "app:action.add": "plus",
  "app:action.archive": "archive",
  "app:action.back": "arrow-left",
  "app:action.browseAttackScenarioLibrary": "database",
  "app:action.cancel": "x-circle",
  "app:action.clear": "x-circle",
  "app:action.close": "x",
  "app:action.confirm": "check",
  "app:action.contactUs": "messages-square",
  "app:action.continue": "play",
  "app:action.copy": "copy",
  "app:action.copyNew": "copy-plus",
  "app:action.delete": "trash-2",
  "app:action.details": "eye",
  "app:action.download": "download",
  "app:action.filter": "list-filter",
  "app:action.login": "log-in",
  "app:action.logout": "log-out",
  "app:action.menu": "menu",
  "app:action.next": "arrow-right",
  "app:action.pause": "pause",
  "app:action.registerAgent": "plug-zap",
  "app:action.reload": "refresh-cw",
  "app:action.reset": "rotate-ccw",
  "app:action.retry": "refresh-cw",
  "app:action.save": "save",
  "app:action.search": "search",
  "app:action.select": "check",
  "app:action.sort": "arrow-up-down",
  "app:action.submitEvaluation": "file-plus-2",
  "app:action.terminate": "square",
  "app:action.upload": "upload",
  "app:action.verify": "shield-check",
  "app:action.viewRecords": "clipboard-list",
  "app:brand.github": "brand:github",
  "app:brand.x": "brand:x",
  "app:contact.address": "map-pin",
  "app:contact.email": "mail",
  "app:contact.phone": "phone",
  "app:contact.social": "messages-square",
  "app:control.collapse": "chevron-up",
  "app:control.expand": "chevron-down",
  "app:control.forward": "chevron-right",
  "app:control.language": "languages",
  "app:control.more": "chevron-down",
  "app:control.selectToggle": "chevrons-up-down",
  "app:control.sidebarClose": "panel-left-close",
  "app:control.sidebarOpen": "panel-left-open",
  "app:attackScenarioLibrary.catalog": "database",
  "app:evaluation.report": "file-bar-chart-2",
  "app:evaluation.runParameters": "sliders-horizontal",
  "app:evaluation.submit": "send",
  "app:field.agent": "bot",
  "app:field.apiKey": "key-round",
  "app:field.connection": "link",
  "app:field.email": "mail",
  "app:field.invokeMode": "workflow",
  "app:field.password": "lock",
  "app:field.passwordConfirm": "shield-check",
  "app:field.submitMethod": "waypoints",
  "app:field.username": "user",
  "app:filter.status": "workflow",
  "app:filter.visibility": "list-filter",
  "app:home.workflow.browse": "database",
  "app:home.workflow.review": "file-search",
  "app:home.workflow.submit": "file-plus-2",
  "app:home.workflow.track": "clipboard-list",
  "app:home.section.confidence": "file-bar-chart-2",
  "app:home.section.contact": "messages-square",
  "app:home.section.attackScenarioLibrary": "database",
  "app:home.section.evaluation": "file-plus-2",
  "app:home.section.evidence": "file-search",
  "app:home.section.privacy": "shield-question",
  "app:home.section.ranking": "trophy",
  "app:home.section.report": "file-bar-chart-2",
  "app:home.section.scope": "list-filter",
  "app:home.section.standard": "shield-check",
  "app:home.section.submit": "send",
  "app:identity.security": "shield-check",
  "app:leaderboard.champion": "trophy",
  "app:method.api": "plug-zap",
  "app:method.docker": "package",
  "app:nav.agents": "bot",
  "app:nav.contact": "messages-square",
  "app:nav.attackScenarios": "database",
  "app:nav.home": "house",
  "app:nav.leaderboard": "trophy",
  "app:nav.profile": "square-pen",
  "app:nav.records": "clipboard-list",
  "app:nav.registerAgent": "plug-zap",
  "app:nav.submit": "file-plus-2",
  "app:status.active": "circle-check-big",
  "app:status.anonymous": "shield-question",
  "app:status.archived": "archive",
  "app:status.available": "file-check-2",
  "app:status.canceled": "ban",
  "app:status.completed": "circle-check-big",
  "app:status.disabled": "ban",
  "app:status.draft": "clock-3",
  "app:status.failed": "triangle-alert",
  "app:status.invalid": "triangle-alert",
  "app:status.notGenerated": "file-minus",
  "app:status.paused": "pause-circle",
  "app:status.pending": "clock-3",
  "app:status.public": "globe",
  "app:status.queued": "clock-3",
  "app:status.rankedOut": "list-x",
  "app:status.ready": "file-check-2",
  "app:status.reportPending": "file-clock",
  "app:status.running": "loader-circle",
  "app:status.terminated": "octagon-x",
  "app:status.verifying": "loader-circle",
  "app:status.warning": "triangle-alert",
  "app:sort.ascending": "arrow-up",
  "app:sort.descending": "arrow-down",
  "app:sort.none": "chevrons-up-down",
} as const satisfies Record<string, AppIconAliasTarget>;

export type AppSemanticIconName = keyof typeof APP_ICON_ALIASES;

export type AppIconName =
  | AppSemanticIconName
  | `brand:${BrandIconName}`
  | `lucide:${LucideIconName}`
  | LucideIconName;

export type ResolvedAppIconName =
  | {
      kind: "brand";
      name: BrandIconName;
      requested: string;
    }
  | {
      kind: "lucide";
      name: LucideIconName;
      requested: string;
    };

const lucideIconNameSet = new Set<string>(LUCIDE_ICON_NAMES);
const brandIconNameSet = new Set<string>(BRAND_ICON_NAMES);

const resolveBrandName = (
  name: string,
  requested: string,
): ResolvedAppIconName => {
  if (brandIconNameSet.has(name)) {
    return {
      kind: "brand",
      name: name as BrandIconName,
      requested,
    };
  }

  return {
    kind: "lucide",
    name: APP_ICON_FALLBACK,
    requested,
  };
};

const resolveLucideName = (
  name: string,
  requested: string,
): ResolvedAppIconName => {
  if (lucideIconNameSet.has(name)) {
    return {
      kind: "lucide",
      name: name as LucideIconName,
      requested,
    };
  }

  return {
    kind: "lucide",
    name: APP_ICON_FALLBACK,
    requested,
  };
};

const resolveAliasTarget = (
  target: AppIconAliasTarget,
  requested: string,
): ResolvedAppIconName => {
  if (target.startsWith("brand:")) {
    return resolveBrandName(target.slice("brand:".length), requested);
  }

  return resolveLucideName(target, requested);
};

export const resolveAppIconName = (icon: string): ResolvedAppIconName => {
  const aliasTarget = APP_ICON_ALIASES[icon as AppSemanticIconName];

  if (aliasTarget) {
    return resolveAliasTarget(aliasTarget, icon);
  }

  if (icon.startsWith("brand:")) {
    return resolveBrandName(icon.slice("brand:".length), icon);
  }

  if (icon.startsWith("lucide:")) {
    return resolveLucideName(icon.slice("lucide:".length), icon);
  }

  return resolveLucideName(icon, icon);
};

export const isKnownAppIconName = (icon: string): boolean => {
  if (icon in APP_ICON_ALIASES) {
    return true;
  }

  if (icon.startsWith("brand:")) {
    return brandIconNameSet.has(icon.slice("brand:".length));
  }

  if (icon.startsWith("lucide:")) {
    return lucideIconNameSet.has(icon.slice("lucide:".length));
  }

  return lucideIconNameSet.has(icon);
};
