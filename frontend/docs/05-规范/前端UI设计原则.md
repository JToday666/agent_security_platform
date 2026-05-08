# 前端 UI 设计原则

本文档用于约束 agents 编写和修改 `frontend/**` 中的用户界面代码。

## 0. 总目标

前端代码必须优先满足以下目标：

1. 用户能明确理解当前页面、任务、数据状态和下一步操作。
2. 用户能在加载、失败、空数据、权限不足、小屏、长文本、慢网络等情况下继续完成任务。
3. 页面结构、组件 API、数据流和状态流足够清晰，便于 agents 安全修改。
4. 优先复用既有组件、tokens、布局模式和业务约定。
5. 不为了局部视觉效果引入复杂实现、重复组件或不可测试逻辑。

## 1. 任务优先

### 原则

页面只呈现完成当前任务所需的信息和操作。平台是评测工具，不是展示型营销页面；页面价值来自任务效率、结果解释和操作确定性。

### 必须遵循

- 首页突出平台定位、核心入口和关键状态。
- 评测创建页只关注：选择数据集、选择 Agent、配置参数、确认提交。
- 评测详情页只关注：运行状态、风险结果、指标解释、日志/样本证据、下一步操作。
- 排行榜只关注：排序、筛选、指标含义、对比依据。
- 报告页只关注：结论、证据、解释、导出。
- 页面文案只保留帮助用户理解当前页面或完成当前操作的信息。

### 禁止

- 在单页堆叠不相关模块。
- 把后台管理、评测运行、数据集维护、报告分析混在一个页面。
- 为了“看起来丰富”加入无任务价值的信息卡、装饰图、复杂布局。
- 在用户页面写入 Mock、Coming Soon、视觉策略、架构说明、开发注释或设计评审文案。

## 2. 设计系统与组件复用优先

### 原则

同一语义只能有一套主要实现。组件、tokens、布局规则优先于临时样式。

### 必须遵循

- 颜色、字号、间距、圆角、阴影、z-index 必须来自 tokens 或既有变量。
- 按钮、输入框、表格、弹窗、抽屉、标签、徽章、分页、Toast、空态、错误态必须优先使用既有组件。
- 新组件必须有明确语义、稳定 props、默认状态和错误状态。
- 同一业务语义使用同一组件，例如：
  - 评测状态统一使用状态徽章组件。
  - 风险等级统一使用风险标签组件。
  - 指标展示统一使用指标卡组件。
  - 页面状态统一使用页面状态组件。

### 禁止

- 为一个页面临时写一套 button、tag、modal、table。
- 硬编码散乱颜色，例如 `#1677ff`、`#999`、`red`。
- 在多个页面复制相似组件后只改少量样式。
- 为局部样式写不可复用的深层选择器覆盖组件内部结构。
- 新增与既有组件语义重复但命名不同的组件。

## 3. 组件成熟度分级

### 原则

组件必须区分临时、业务、稳定和废弃状态，避免历史 UI 无序堆积。

| 等级         | 含义         | 使用规则                             |
| ------------ | ------------ | ------------------------------------ |
| Experimental | 临时验证组件 | 只允许在单一实验页面或任务范围内使用 |
| Business     | 业务组件     | 可在同一业务域复用                   |
| Stable       | 稳定基础组件 | 可跨模块使用，API 不得随意破坏       |
| Deprecated   | 废弃组件     | 不得新增使用，必须标注替代方案       |

### 必须遵循

- Stable 组件变更必须兼容旧调用，除非同步完成迁移。
- Deprecated 组件必须写明替代组件。
- Agent 修改组件时必须检查影响范围，不能只看当前页面。
- 新组件从 Business 开始沉淀；只有跨模块稳定复用后才能视为 Stable。

## 4. 语义 HTML 优先

### 原则

优先使用浏览器原生语义和行为，不用 `div/span` 模拟交互控件。

### 必须遵循

- 点击操作用 `<button>`。
- 页面跳转用 `<a>` 或路由链接。
- 表单字段必须有 `<label>` 或等价 accessible name。
- 数据表格使用 `<table>` 语义或具备等价语义的表格组件。
- 页面结构使用 `header / main / nav / section / article / footer`。
- 图标按钮必须提供 accessible name。
- 可交互元素必须有可见 focus 状态。

### 禁止

```html
<div @click="submit">提交</div>
<span role="button">删除</span>
<input placeholder="请输入名称" />
```

### 正确

```html
<button type="button" @click="submit">提交</button>

<label for="dataset-name">数据集名称</label>
<input id="dataset-name" name="datasetName" />
```

## 5. ARIA 谨慎使用

### 原则

ARIA 只补充语义，不补充行为。能用原生 HTML 时，不使用 ARIA 模拟。

### 必须遵循

- 使用 `role` 后，必须实现该 role 对应的键盘行为。
- `aria-label`、`aria-describedby`、`aria-invalid`、`aria-live` 只在语义需要时使用。
- 表单错误必须与字段关联。
- 状态消息必须能被辅助技术感知。
- 自定义菜单、弹窗、抽屉、tab、combobox 等复杂组件必须符合对应键盘交互预期。

### 禁止

```html
<div role="button">提交</div>
```

除非同时实现：

- `tabindex="0"`
- Enter / Space 触发
- disabled 状态处理
- focus 样式
- accessible name

通常应直接使用：

```html
<button type="button">提交</button>
```

## 6. 状态必须完整且确定

### 原则

所有异步、可失败、可为空、可禁用、受权限控制的 UI 都必须有明确状态。

### 必须覆盖

- idle
- loading
- success
- error
- empty
- disabled
- forbidden
- timeout
- partial failure

### 必须遵循

- 用户点击后立即显示反馈。
- loading 时防止重复提交。
- error 显示原因和可执行下一步。
- empty 显示空态说明和引导操作。
- disabled 说明原因，不能只变灰。
- 后端长任务必须显示等待、运行中、成功、失败、取消、超时等状态。
- 局部模块失败不得导致整个页面空白。

### 禁止

```vue
<button :disabled="loading" @click="submit">提交</button>
<div>{{ data }}</div>
```

### 正确

```vue
<UiButton
  :loading="isSubmitting"
  :disabled="isSubmitting || !canSubmit"
  @click="submitEvaluation"
>
  {{ isSubmitting ? '提交中' : '提交评测' }}
</UiButton>

<PageStatePanel v-if="isLoading" state="loading" />
<PageStatePanel
  v-else-if="error"
  state="error"
  :message="error.message"
  retry
/>
<EmptyState
  v-else-if="items.length === 0"
  title="暂无评测记录"
  action="创建评测"
/>
<EvaluationList v-else :items="items" />
```

## 7. 微交互与微光效规范 (Micro-interactions & Lighting)

### 原则

动效与光影必须服务于任务反馈、状态明确与层级暗示。优先使用系统级的 Tokens。

### 必须遵循

- 可点击元素（按钮、链接、卡片）应当有明确聚焦（Focus）与悬浮（Hover）的视觉反馈，如位移 `translateY`、光斑、倒角阴影变化。
- 弹出框、菜单等浮层组件的入场动画采用弹性缓动函数（如 `var(--ease-spring)`）或强调缓动（`var(--ease-emphasized)`）。
- 深色背景或强调级卡片周边使用系统级的内倒角变量（如 `var(--glass-border-inset)`）以增强边缘立体质感，结合合适的 `backdrop-filter`。
- 杜绝无关任务、纯装饰目的且耗费性能的大面积背景持续动效。

## 8. 内容原子性与文本韧性

### 原则

UI 必须能承受长文本、长 ID、多语言长度差异、异常数据和小屏宽度。

### 必须遵循

- 按钮、标签、徽章、状态 pill、数字单位不得折行。
- 长标题、长路径、长模型名、长 Agent 名称、长数据集名称必须有处理策略。
- 长 ID 使用等宽字体、截断、复制按钮或详情展开。
- 核心内容不得因为容器变窄而直接丢失。
- 文案区域不得只按中文短文本设计宽度。
- 当前不要求实现完整 i18n 或 RTL，但不得制造明显阻碍未来国际化的固定宽度和硬编码布局。

### 推荐策略

| 内容类型          | 推荐处理                            |
| ----------------- | ----------------------------------- |
| 按钮文案          | 不换行，必要时换更短文案            |
| 状态标签          | 不换行，不压缩变形                  |
| 评测 ID / 运行 ID | 中间截断 + 复制                     |
| Agent 名称        | 单行截断 + tooltip 或详情页完整展示 |
| 数据集描述        | 可换行，必要时折叠/展开             |
| 错误信息          | 可换行，保留完整含义                |
| 报告结论          | 可换行，不截断                      |
| 表格单元格        | 关键列固定，说明列可换行或展开      |

### 推荐样式

```scss
.atomic {
  white-space: nowrap;
  flex-shrink: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.long-text {
  overflow-wrap: anywhere;
}

.mono-id {
  font-family: var(--font-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

## 8. CSS-first 响应式

### 原则

布局自适应优先使用 CSS，不默认使用 JS 监听尺寸。

### 优先使用

- Flexbox
- Grid
- Media Query
- Container Query
- `minmax()`
- `clamp()`
- `fit-content`
- `max-width: 100%`
- tokens 化 spacing
- 合理 overflow

### 禁止默认使用

- `window.resize` 驱动普通布局。
- 频繁读取 `getBoundingClientRect()` 驱动普通布局。
- 用 `ResizeObserver` 模拟普通断点。
- 用 `IntersectionObserver` 模拟布局断点。
- 用 JS 根据宽度增删 class 实现常规响应式。

### 允许例外

以下场景可以使用 JS 尺寸监听、可见性监听或 DOM 测量：

- 虚拟列表。
- 图表 canvas。
- 拖拽分栏。
- 编辑器。
- 复杂数据表格列宽计算。
- 第三方组件必须读取真实尺寸。
- 图片、日志或长列表的可视区懒加载。
- 无限滚动。

### 例外要求

必须写注释说明：

```ts
// Layout exception:
// CSS/container query cannot solve this because the chart must measure
// the rendered container before recalculating canvas dimensions.
// Keep observer scoped and debounce expensive work.
```

## 9. 数据密集页面优先可读

### 原则

评测平台是数据密集型系统，表格、指标、日志、报告必须优先保证可读、可比、可解释。

### 必须遵循

- 数字指标右对齐或按统一规则对齐。
- 同类指标保留统一精度。
- 风险等级、评测状态、任务状态使用固定颜色和固定文案。
- 指标必须提供简短解释，尤其是综合分、风险命中率、失败率、置信区间等。
- 表格必须支持必要的排序、筛选、分页或虚拟化。
- 重要结论必须可追溯到样本、日志或证据。
- 日志和样本内容必须支持长文本查看，不得破坏整体布局。

### 禁止

- 同一指标在不同页面使用不同名称。
- 同一状态在不同页面使用不同颜色。
- 表格列过多但没有分组、隐藏、展开或详情页。
- 只展示分数，不解释分数含义。
- 将关键判断只藏在颜色里，不提供文字或图标辅助。

## 10. 表单必须防错

### 原则

表单不是输入框堆叠，而是带校验、引导、确认和恢复能力的任务流程。

### 必须遵循

- 必填字段必须明确标记。
- 校验错误必须靠近字段显示。
- 提交前能检查的错误，不等后端失败后才提示。
- 危险操作必须确认。
- 删除、覆盖、重跑、取消评测等操作必须说明影响范围。
- 用户已输入内容不得因切换 tab、刷新局部状态、接口失败而意外丢失。
- 表单提交中必须禁用重复提交路径。
- 表单依赖项变化时，必须明确清空、保留或重新校验受影响字段。

### 错误文案要求

错误文案必须包含：

1. 发生了什么。
2. 为什么可能发生。
3. 用户下一步能做什么。

### 示例

不合格：

```txt
提交失败
```

合格：

```txt
提交失败：当前 Agent 连接校验未通过。请检查回调地址和鉴权配置后重试。
```

## 11. 无障碍是完成标准

### 原则

页面完成标准包括无障碍，不是视觉完成后再补。

### 最低要求

- 普通文本对比度 ≥ 4.5:1。
- 大文本对比度 ≥ 3:1。
- 交互目标 ≥ 24×24 CSS px，或满足足够间距例外。
- 所有交互元素可键盘访问。
- focus 必须可见。
- focus 不得被 sticky header、footer、悬浮面板完全遮挡。
- 表单错误必须有文本说明。
- 图标按钮必须有可访问名称。
- 弹窗、抽屉、菜单必须处理 focus 进入、恢复和 Esc 关闭。
- 状态变更应在必要时通过 `aria-live` 或组件机制通知辅助技术。
- 颜色不能作为唯一信息载体，必须配合文本、图标或形状。

### 禁止

```scss
*:focus {
  outline: none;
}
```

### 正确

```scss
:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
```

## 12. 性能预算

### 原则

页面不能因为组件复杂、依赖过重或渲染过量而影响关键任务。

### 必须遵循

- 路由页面懒加载。
- 大型依赖必须评估体积和收益。
- 大表格必须分页、懒加载或虚拟化。
- 图片、图表、异步内容必须预留尺寸，避免明显布局抖动。
- 复杂计算不得放在模板表达式中反复执行。
- 高频事件必须节流、去抖或迁移到更合适的数据流。
- 不为纯视觉效果引入大型依赖。
- 加载中必须有明确状态，不得长时间空白。
- 日志、报告、样本等大文本内容应按需加载或分块展示。

### 禁止

- 首屏加载所有路由页面。
- 无限制渲染全量日志、全量样本、全量评测结果。
- 在 `scroll`、`resize`、`mousemove` 中直接执行重计算。
- 在渲染阶段解析大 JSON 或做复杂统计。
- 加载过程中页面空白无状态。

## 13. 前端安全边界

### 原则

前端不得执行、拼接、信任来自后端或用户的非可信内容。

### 必须遵循

- Vue 模板必须由项目代码控制。
- 用户输入、后端返回的报告正文、日志、错误信息默认按文本渲染。
- 禁止默认使用 `v-html`。
- 必须展示富文本时，先经过可信白名单清洗。
- URL、文件名、下载地址、跳转地址必须校验。
- token、secret、API key 不得出现在前端代码、localStorage、sessionStorage、日志、URL query 中。
- 权限控制以后端为准，前端只做体验层隐藏和提示。
- 用户可下载内容必须明确文件名、类型和来源。

### 禁止

```vue
<div v-html="backendReportHtml"></div>
```

除非已经经过可信清洗，并说明允许的标签、属性和 URL 协议。

## 14. 类型与数据契约优先

### 原则

Agent 写代码时必须依赖清晰类型，而不是猜字段、猜状态、猜接口返回。

### 必须遵循

- API 返回值必须有 TypeScript 类型。
- 枚举状态必须定义为 union 或 enum。
- 组件 props 和 emits 必须明确类型。
- 可为空字段必须显式处理。
- 后端字段名不得在页面中到处散落，应通过 API 层或 mapper 收敛。
- 金额、比例、分数、时间、状态必须有统一 formatter。
- 指标含义和显示格式必须稳定，不得在不同页面各自实现。

### 示例

```ts
type EvaluationStatus =
  | "pending"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "timeout";

interface EvaluationSummary {
  id: string;
  name: string;
  status: EvaluationStatus;
  score: number | null;
  riskCount: number;
  createdAt: string;
}
```

## 15. 页面级状态统一

### 原则

所有页面使用统一状态模型，避免每个页面自创 loading、error、empty 表现。

| 状态      | 使用场景             |
| --------- | -------------------- |
| loading   | 首次加载、局部刷新   |
| empty     | 无数据但系统正常     |
| error     | 接口失败或解析失败   |
| forbidden | 无权限               |
| not-found | 资源不存在           |
| stale     | 数据可能过期         |
| partial   | 部分数据加载失败     |
| timeout   | 长任务或接口超时     |
| offline   | 网络不可用或连接中断 |

### 必须遵循

- 页面级错误用统一页面状态组件。
- 局部模块错误用模块级错误组件。
- 空态必须给出下一步。
- 权限不足必须说明需要什么权限或联系谁。
- 部分失败不能把整个页面变成空白。
- 长任务状态必须可刷新、可重试或可返回列表。

## 16. 文案和术语一致

### 原则

安全评测平台的术语必须稳定，避免同一概念多种叫法。

| 概念        | 推荐文案 |
| ----------- | -------- |
| evaluation  | 评测     |
| agent       | Agent    |
| dataset     | 数据集   |
| run         | 运行     |
| report      | 报告     |
| risk        | 风险     |
| score       | 分数     |
| benchmark   | 基准     |
| sample      | 样本     |
| trace / log | 日志     |
| status      | 状态     |
| ranking     | 排行榜   |
| metric      | 指标     |

### 禁止

- “评估”“测评”“评价”混用。
- “机器人”“智能体”“Agent”混用；项目中建议固定为 “Agent”。
- “危险”“风险”“漏洞”无区分混用。
- 按钮文案使用含糊动词，例如“处理”“操作”“执行一下”。
- 错误提示只写“失败”“异常”“错误”。

## 17. Agent 修改代码的最小变更原则

### 原则

Agent 应做能完成任务的最小安全变更，不进行无关重构。

### 必须遵循

- 修改前先识别现有组件、tokens、API 层和状态模型。
- 优先局部修复，不重写整个页面。
- 不改无关格式。
- 不引入无关依赖。
- 不改变公共组件 API，除非同步迁移所有调用。
- 修改涉及 UI 状态时，必须检查 loading、error、empty、disabled、forbidden。
- 修改涉及表单时，必须检查校验、提交、防重复、错误反馈。
- 修改涉及表格时，必须检查分页、排序、空态、长文本。
- 修改涉及权限时，必须检查前端提示和后端权限边界是否一致。
- 修改涉及报告、日志、样本时，必须检查大文本、换行、复制、展开和性能。
