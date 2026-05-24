# Backend TODO

只维护未完成事项、优先级和阻塞项。当前能力看 [README.md](./README.md)，文档边界看 [docs/05-规范/文档维护约定.md](./docs/05-规范/文档维护约定.md)。

以下待办基于当前仓库现状整理。当前已经具备：

- `auth / user / datasets / agents / evaluations / scoring / difficulty / leaderboards` 后端模块与公开接口
- Agent 模板、注册、详情、列表、真实轻量验证、归档和凭据脱敏存储
- `test_runs / run_datasets / run_samples / sample_executions` 任务图创建
- worker 轮询认领、心跳、暂停/恢复/取消/终止、任务级摘要报告
- `settings.worker_workdir_root` 工作目录准备、probe backend 拉起、`external_agent_api / synthetic_local` dispatch
- `sample_oracles` 规则入库，运行结束后生成 `oracle_results` 与 `execution_summaries`
- `run_reports.summary_json` 聚合、评测评分重算/查询、动态难度版本重算/发布、排行榜快照/查询

当前“部分实现但仍未生产闭环”的能力：

- `submit_method = "api"` 已开放，worker 会按冻结 Agent 配置真实调用外部 API Agent；Docker 提交能力仍不开放
- `execution_artifacts` 当前覆盖 runtime 元信息、事件日志、编译/回放结果、回放报告等基础产物，仍缺 richer evidence
- `llm_judge` 已接入 OpenAI-compatible Chat Completions，但缺配置、调用失败、输出不合法、低置信或模型要求复核时仍保守进入待复核
- `sample_difficulty_stats` 已有运行后基础回刷逻辑，难度版本可重算/发布；仍缺长期观测、审计和自动化治理策略
- `run_reports` 当前只产出 `summary_json`，`report_uri` 仍为空；在线报告读取接口已开放

## 当前优先

- [ ] 完善真实 Agent API 调用链路：补齐调用日志、失败分类、状态观测、外部响应证据归档和更细的超时语义
- [ ] 补齐样本级结果查询接口：提供 run 下 execution 列表、单 execution 详情和产物索引
- [ ] 生成可下载报告：为 `run_reports` 产出 `report_uri`，补齐典型样本引用和更细粒度统计
- [ ] 为 worker 增加启动/停止观测、健康检查、告警与异常恢复
- [ ] 接入真实 Docker 运行链路：为 `submit_method = "docker"` 落地镜像拉起、认证信息注入、生命周期清理和运行期隔离

## 后续事项

- [ ] 实现真实重试链路：为执行级失败重试、重试策略配置和 `retry_no > 0` 落地生产逻辑
- [ ] 完善难度治理：增加难度回刷审计、版本对比、发布审批和异常样本识别
- [ ] 丰富 `execution_artifacts`：覆盖网络请求、页面访问、工具调用、stdout/stderr、更多截图/trace 产物
- [ ] 为样本目录补充更稳定的 manifest / 启动约定，统一入口暴露、辅助服务和依赖声明
- [ ] 评估 PostgreSQL 轮询是否需要升级为专用队列
- [ ] 增加生产安全基线：启动时校验生产强密钥、凭据加密方案标准化、运行期敏感文件清理策略

## 已知阻塞 / 依赖

- 真实 Agent 执行链已具备基础调用适配；后续质量依赖更完整的调用观测、失败分型和外部证据归档
- 自动 oracle 判定依赖样本侧持续补齐结构化 `evaluator_type / evaluator_config`；未结构化样本仍需人工复核兜底
- Docker 运行链依赖镜像拉起、凭证管理、运行期网络/文件隔离与清理策略成套落地
- 难度治理依赖更稳定的 `oracle_results / execution_summaries` 历史数据，以及面向发布的审计与回滚策略
