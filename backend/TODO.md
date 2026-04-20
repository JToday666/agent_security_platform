# Backend TODO

只维护未完成事项。当前能力看 [README.md](./README.md)，文档边界看 [docs/05-规范/文档维护约定.md](./docs/05-规范/文档维护约定.md)。

以下待办基于 `2026-04-21` 的仓库现状整理。当前已经具备：

- `auth / user / datasets / agents / evaluations` 五组基础接口
- `test_runs / run_datasets / run_samples / sample_executions` 任务图创建
- worker 轮询认领、心跳、暂停/恢复/取消/终止、任务级摘要报告
- `runtime/workdir` 工作目录准备、probe backend 拉起、`synthetic_local` dispatch
- `execution_artifacts` 基础落库，`execution_summaries` 摘要写回，`run_reports.summary_json` 聚合

当前“部分实现但仍未闭环”的能力：

- `submit_method = "api" / "docker"`、`credential_ref`、`execution_config` 已开放并落库，但 worker 还不会真实消费它们
- `execution_artifacts` 当前覆盖 runtime 元信息、事件日志、编译/回放结果、回放报告等基础产物，仍缺 richer evidence
- `run_reports` 当前只产出 `summary_json`，`report_uri` 仍为空

## 当前优先

- [ ] 接入真实 Agent API 调用链路：按 `submit_method = "api"` 读取 `agent_base_url / credential_ref`，补齐超时、失败分类、调用日志与状态流转
- [ ] 接入真实 Docker 运行链路：为 `submit_method = "docker"` 落地镜像拉起、认证信息注入、生命周期清理和运行期隔离
- [ ] 落地结构化 evaluator / oracle 执行链路：消费 `sample_oracles.evaluator_type / evaluator_config`，生成 `oracle_results`
- [ ] 补齐样本级结果查询接口：提供 run 下 execution 列表、单 execution 详情、产物索引和独立报告入口
- [ ] 生成可下载报告：为 `run_reports` 产出 `report_uri`，补齐典型样本引用和更细粒度统计

## 后续事项

- [ ] 实现真实重试链路：让 `retryEnabled` 不只停留在 `execution_config` 和 `retry_no = 0`
- [ ] 回刷样本难度统计：根据历史执行结果更新 `sample_difficulty_stats` 和 `benchmark_samples.difficulty_score`
- [ ] 丰富 `execution_artifacts`：覆盖网络请求、页面访问、工具调用、stdout/stderr、更多截图/trace 产物
- [ ] 为样本目录补充更稳定的 manifest / 启动约定，统一入口暴露、辅助服务和依赖声明
- [ ] 为 worker 增加启动/停止观测、健康检查、告警与异常恢复，并评估 PostgreSQL 轮询是否需要升级为专用队列

## 已知阻塞 / 依赖

- 真实 Agent 执行链依赖统一的目标适配层；当前 `synthetic_local` 与 `deferred` 只解决了 runtime 闭环和等待 finalize 的框架问题
- 自动 oracle 判定依赖样本侧逐步补齐结构化 `evaluator_type / evaluator_config`；未结构化样本仍需人工复核兜底
- Docker 运行链依赖镜像拉起、凭证管理、运行期网络/文件隔离与清理策略成套落地
- 难度统计回刷依赖 `oracle_results / execution_summaries` 的稳定生产，当前缺少可复用的真实判定数据
