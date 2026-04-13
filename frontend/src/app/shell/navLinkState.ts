import type { AppNavItem } from "./NavItems";

export const getNavLinkStateProps = (item: AppNavItem) =>
  item.exact
    ? { activeClass: "active", exactActiveClass: "active" }
    : { activeClass: "active" };
