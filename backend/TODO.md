# Backend TODO

只维护未完成事项。当前能力看 [README.md](./README.md)，文档边界看 [docs/05-规范/文档维护约定.md](./docs/05-规范/文档维护约定.md)。
以下待办基于 `2026-04-09` 的仓库现状整理：`auth / user / datasets / agents / evaluations` 基础接口、run 快照、`sample_executions` 创建、worker 轮询、暂停/恢复/取消/终止和报告摘要已具备；当前缺口主要在真实执行编排、证据采集与样本级结果查询。

## 当前优先

- [ ] 将 `app.worker.execution` 从模拟判定切换为真实执行编排：为 `sample_executions` 准备 `work_dir` / `environment_ref` / `entry_url`，按样本复制站点副本并支持本地页面或辅助服务启动
- [ ] 接入真实 Agent 调用链路：按 `submit_method` 调用 API / Docker 目标，补齐超时、失败分类、受控重试和 `sample_executions.status` 状态流转
- [ ] 落地 `execution_artifacts` 采集与落库：至少覆盖日志、页面访问、网络请求、工具调用和关键运行产物，并统一存储路径约定
- [ ] 落地 evaluator / oracle 执行链路：将当前模拟 `success_oracle` / `harm_oracle` 结果切换为结构化分析器，优先支持文本、URL/网络、DOM/行为等基础 evaluator，并保留人工复核兜底
- [ ] 补齐样本级结果查询接口：提供 run 下 execution 列表、单 execution 详情和独立报告查询接口，支撑前端查看证据、产物和报告入口

## 后续事项

- [ ] 为样本目录补充统一 manifest / 启动约定，明确静态资源、辅助服务、入口暴露和依赖声明的标准格式
- [ ] 明确 `entry_url` 为空时的统一回退解析规则，并与样本导入约定保持一致
- [ ] 将自然语言 oracle 逐步拆成可程序判定的 `evaluator_type` / `evaluator_config`，沉淀可复用 evaluator registry
- [ ] 丰富任务报告产物：生成可下载的 `report_uri`、典型样本引用以及按数据集/风险维度展开的统计明细
- [ ] 为 worker 增加启动/停止观测、健康检查、心跳告警与异常恢复策略，并评估 PostgreSQL 轮询是否需要升级为专用队列

## 已知阻塞/依赖

- 真实执行链路依赖环境层补齐 execution 副本准备、URL 暴露、产物采集和清理接口约定
- 自动 oracle 判定依赖样本侧逐步补齐结构化 `evaluator_type` / `evaluator_config`；未结构化样本需要人工复核兜底
- `submit_method = "docker"` 已开放提交契约，但实际镜像拉起、凭证注入和运行期清理链路尚未落地
