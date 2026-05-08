<template>
  <component
    :is="iconComponent"
    v-bind="attrs"
    :size="size"
    :title="title"
    :aria-hidden="decorative ? 'true' : undefined"
    :role="decorative ? undefined : 'img'"
  />
</template>

<script setup lang="ts">
import {
  AlertTriangle,
  Archive,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowUpDown,
  Ban,
  Bot,
  BotMessageSquare,
  Check,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  ChevronsUpDown,
  CircleCheckBig,
  ClipboardList,
  Clock3,
  Copy,
  CopyPlus,
  Database,
  Download,
  Eye,
  FileBarChart2,
  FileCheck2,
  FileClock,
  FileMinus,
  FilePlus2,
  FileSearch,
  Globe,
  House,
  KeyRound,
  Link,
  List,
  ListFilter,
  ListX,
  LoaderCircle,
  Lock,
  LogIn,
  LogOut,
  Mail,
  MapPin,
  Menu,
  MessagesSquare,
  OctagonX,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Pause,
  PauseCircle,
  Phone,
  Play,
  PlugZap,
  Plus,
  RefreshCw,
  RotateCcw,
  RotateCw,
  Save,
  Search,
  Send,
  ShieldCheck,
  ShieldQuestion,
  SlidersHorizontal,
  Square,
  SquarePen,
  Trash2,
  TriangleAlert,
  Trophy,
  Upload,
  User,
  Waypoints,
  Workflow,
  X,
  XCircle,
} from "lucide-vue-next";
import { computed, useAttrs, type Component } from "vue";

defineOptions({
  inheritAttrs: false,
});

const props = withDefaults(
  defineProps<{
    icon: string;
    size?: string | number;
    decorative?: boolean;
    title?: string;
  }>(),
  {
    size: "1em",
    decorative: true,
    title: undefined,
  },
);

const lucideIcons: Record<string, Component> = {
  "alert-triangle": AlertTriangle,
  archive: Archive,
  "arrow-down": ArrowDown,
  "arrow-left": ArrowLeft,
  "arrow-right": ArrowRight,
  "arrow-up": ArrowUp,
  "arrow-up-down": ArrowUpDown,
  ban: Ban,
  bot: Bot,
  "bot-message-square": BotMessageSquare,
  check: Check,
  "chevron-down": ChevronDown,
  "chevron-right": ChevronRight,
  "chevron-up": ChevronUp,
  "chevrons-up-down": ChevronsUpDown,
  "circle-check-big": CircleCheckBig,
  "clipboard-list": ClipboardList,
  "clock-3": Clock3,
  copy: Copy,
  "copy-plus": CopyPlus,
  database: Database,
  download: Download,
  eye: Eye,
  "file-bar-chart-2": FileBarChart2,
  "file-check-2": FileCheck2,
  "file-clock": FileClock,
  "file-minus": FileMinus,
  "file-plus-2": FilePlus2,
  "file-search": FileSearch,
  globe: Globe,
  house: House,
  "key-round": KeyRound,
  link: Link,
  list: List,
  "list-filter": ListFilter,
  "list-x": ListX,
  "loader-circle": LoaderCircle,
  lock: Lock,
  "log-in": LogIn,
  "log-out": LogOut,
  mail: Mail,
  "map-pin": MapPin,
  menu: Menu,
  "messages-square": MessagesSquare,
  "octagon-x": OctagonX,
  package: Package,
  "panel-left-close": PanelLeftClose,
  "panel-left-open": PanelLeftOpen,
  pause: Pause,
  "pause-circle": PauseCircle,
  phone: Phone,
  play: Play,
  "plug-zap": PlugZap,
  plus: Plus,
  "refresh-cw": RefreshCw,
  "rotate-ccw": RotateCcw,
  "rotate-cw": RotateCw,
  save: Save,
  search: Search,
  send: Send,
  "shield-check": ShieldCheck,
  "shield-question": ShieldQuestion,
  "sliders-horizontal": SlidersHorizontal,
  square: Square,
  "square-pen": SquarePen,
  "trash-2": Trash2,
  "triangle-alert": TriangleAlert,
  trophy: Trophy,
  upload: Upload,
  user: User,
  waypoints: Waypoints,
  workflow: Workflow,
  x: X,
  "x-circle": XCircle,
};

const normalizeLucideName = (icon: string): string =>
  icon.startsWith("lucide:") ? icon.slice("lucide:".length) : icon;

const attrs = useAttrs();
const iconComponent = computed(
  () => lucideIcons[normalizeLucideName(props.icon)] ?? CircleCheckBig,
);
</script>
