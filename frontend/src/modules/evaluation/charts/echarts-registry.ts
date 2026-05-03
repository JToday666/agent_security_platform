import { use } from "echarts/core";
import {
  BarChart,
  LineChart,
  PieChart,
  RadarChart,
  ScatterChart,
} from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

let registered = false;

export const ensureEvaluationChartsRegistered = () => {
  if (registered) {
    return;
  }

  use([
    BarChart,
    LineChart,
    PieChart,
    RadarChart,
    ScatterChart,
    DataZoomComponent,
    GridComponent,
    LegendComponent,
    RadarComponent,
    TooltipComponent,
    CanvasRenderer,
  ]);
  registered = true;
};
