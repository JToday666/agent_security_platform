# Frontend 清理 TODO

说明：本清单只记录 frontend 范围内已确认或高置信的冗余、过期声明、无效代码/文件和工程隐患。优先处理会影响数据正确性、用户可见状态和提交链路的项。

## P0 高优先级

- [ ] 统一评测状态来源、筛选项和展示映射
  - 问题：`EvaluationStatus`、筛选器、状态标签、服务视图和 mock 的状态分支不完全一致。`queued`、`pausing`、`terminating`、`canceling` 已在状态来源里出现，但 `EvaluationFilterBar.vue` 的筛选项没有完整覆盖；`StatusTag.vue` 里这些中间态当前还会落到失败图标分支，图标和 tone 也依赖分散分支，后续很容易再次漂移。
  - 待修改文件：
    - `src/modules/evaluation/components/EvaluationFilterBar.vue`
    - `src/modules/evaluation/lib/evaluation-record-filters.ts`
    - `src/shared/ui/display/StatusTag.vue`
    - `src/modules/evaluation/lib/evaluation-status.ts`
    - `src/modules/evaluation/api/internal/evaluation-service-view.ts`
    - `src/modules/evaluation/api/internal/mock-evaluation-api.ts`
    - `src/modules/evaluation/components/EvaluationRecordItem.vue`
  - 建议动作：抽一个单一状态元数据源，统一生成筛选项、文案、tone 和 icon；补齐新增状态的筛选选项和展示；增加针对状态映射和筛选结果的测试。
  - 验证点：记录列表中每个状态都能筛到；`queued`、`pausing`、`terminating`、`canceling` 不会被误显示成失败图标。

- [ ] 处理 `docker.envText` 遗留字段
  - 问题：`SubmitFormState.docker.envText` 只在草稿 store 里初始化，没有进入提交快照，也没有进入最终 payload；当前要么是完全无效的残留字段，要么是丢失了 Docker 提交的环境变量输入能力。
  - 待修改文件：
    - `src/modules/submission/stores/submitDraftStore.ts`
    - `src/shared/types/agent-types.ts`
    - `src/modules/submission/model/submit-payload-snapshot.ts`
    - `src/modules/submission/components/SubmitBasicInfoForm.vue`
    - `src/modules/submission/model/parameter-validator.ts`
  - 建议动作：如果不支持环境变量输入，删除该字段及相关分支；如果要支持，补上表单输入、序列化和校验，确保最终 payload 中有真实的 `env` 数据。
  - 验证点：提交表单里用户输入的 Docker 环境变量不会丢失；如果决定移除，相关类型和 store 不再保留废字段。

- [ ] 确认是否保留 `evaluation-report-view.ts` 作为公共入口
  - 问题：当前在 `frontend/src` 内没有发现对这个 barrel 文件的引用，它只是把四个实现文件重新导出一层，维护成本高于直接引用具体模块。
  - 待修改文件：
    - `src/modules/evaluation/lib/evaluation-report-view.ts`
    - 所有实际 import 该入口的文件（若存在外部或后续新增引用）
  - 建议动作：如果没有外部依赖，删除该文件并把调用方改为直接引用具体实现；如果它是刻意保留的稳定入口，补一条说明，避免别人把它误当成业务层。
  - 验证点：删除后没有任何 import 报错，或入口存在时有明确用途。

## P1 中优先级

- [ ] 清理无引用的通用样式工具类
  - 问题：`utilities.scss` 中有几类工具样式目前未找到实际使用痕迹，属于典型“先建了、后来没落地”的冗余 CSS。
  - 待修改文件：
    - `src/app/styles/utilities.scss`
  - 候选类：
    - `grid-cols-3`
    - `flex-gap-1`
    - `flex-gap-2`
    - `badge-base`
    - `line-clamp-2`
    - `line-clamp-3`
  - 建议动作：再做一次定向搜索，确认是否存在动态 class 拼接或外部模板消费；若无，就删除这些类，避免样式文件持续膨胀。
  - 验证点：页面和组件没有丢失布局；保留的工具类仍有明确调用点。

- [ ] 处理 `StatusTag` 的 `report` 语义分支
  - 问题：`StatusTag.vue` 声明了 `kind="report"` 的使用场景，但组件内部没有独立的 `report` 分支，当前会落入通用兜底逻辑；这会让“报告可用 / 缺失 / 处理中”的语义被压扁。
  - 待修改文件：
    - `src/shared/ui/display/StatusTag.vue`
    - `src/modules/evaluation/components/EvaluationSummaryBand.vue`
    - `src/modules/evaluation/lib/evaluation-detail-view.ts`
  - 建议动作：给 report 单独建分支，或者把外部调用改成更明确的 kind/value 组合；确保 `available` / `pending` / `missing` 的图标、颜色和文案可读。
  - 验证点：评测摘要里的报告状态能清楚区分“已生成、等待生成、缺失”。

## P2 低优先级 / 结构收敛

- [ ] 复核 `DatasetCategoryViewModel` 是否仍需要别名层
  - 问题：`DatasetCategoryViewModel` 只是 `DatasetCategory` 的别名，当前被多个组件和工具函数使用。它本身不算错误，但如果不再承担“视图模型”和“原始模型”分层，就只是额外的命名负担。
  - 待修改文件：
    - `src/shared/types/dataset-types.ts`
    - `src/modules/dataset/lib/dataset-utils.ts`
    - `src/modules/dataset/model/dataset-catalog-view.ts`
    - `src/modules/dataset/components/DatasetFilterBar.vue`
    - `src/modules/dataset/components/DatasetCategorySection.vue`
    - `src/modules/dataset/components/DatasetSubcategoryCard.vue`
    - `src/modules/submission/components/SubmitDatasetCategoryList.vue`
    - `src/modules/submission/components/SubmitDatasetPanel.vue`
    - `src/modules/submission/components/SubmitDatasetCategoryBlock.vue`
  - 建议动作：先判断它是否仍代表独立语义层；如果只是历史遗留，可逐步并回 `DatasetCategory`，减少类型层的心智负担。
  - 验证点：类型替换后没有丢失可读性，也不引入大范围机械修改。
