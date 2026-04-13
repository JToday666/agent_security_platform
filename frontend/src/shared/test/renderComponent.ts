import { h, render, type Component } from "vue";

interface RenderComponentOptions {
  props?: Record<string, unknown>;
  slots?: Record<string, (() => unknown) | string>;
}

export const renderComponent = (
  component: Component,
  options: RenderComponentOptions = {},
) => {
  const container = document.createElement("div");
  document.body.appendChild(container);

  render(
    h(component as never, options.props ?? {}, options.slots ?? {}),
    container,
  );

  return {
    container,
    unmount() {
      render(null, container);
      container.remove();
    },
  };
};
