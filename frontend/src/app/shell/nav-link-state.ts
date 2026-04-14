import type { AppNavItem } from "./nav-items";

export const getNavLinkStateProps = (item: AppNavItem) =>
  item.exact
    ? { activeClass: "active", exactActiveClass: "active" }
    : { activeClass: "active" };
