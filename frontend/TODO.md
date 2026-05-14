# Frontend 清理 TODO

说明：本清单只记录 frontend 范围内已确认或高置信的冗余、过期声明、无效代码/文件和工程隐患。优先处理会影响数据正确性、用户可见状态和提交链路的项。

## P0 高优先级

## P1 中优先级

## P2 低优先级 / 结构收敛

- [ ] 后续确认旧 dataset ID alias 是否可以移除
  - 问题：`dataset-id-aliases.ts` 仍被 API、展示和 mock 链路使用；当前无法确认后端是否还会返回 `A1`、`B1` 等旧 ID。
  - 待修改文件：
    - `src/modules/dataset/model/dataset-id-aliases.ts`
    - 所有调用 `normalizeDatasetId` / `normalizeDatasetIds` 的文件
  - 建议动作：确认后端和历史数据不再返回旧 ID 后，再删除 alias map 和相关调用；确认前继续保留，避免详情页、报告和 mock 数据解析退化。
  - 验证点：删除后旧 ID 不再出现在接口、mock、URL、报告样本和本地存储数据中。
