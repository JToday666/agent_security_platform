# agent_security_platform

前端目录

```text
frontend/
├── env.d.ts                          # Vite 环境类型声明
├── index.html                        # 前端入口 HTML
├── package.json                      # 前端脚本与依赖
├── package-lock.json                 # npm 锁文件
├── tsconfig.app.json                 # 应用 TS 配置
├── tsconfig.json                     # TS 工程入口
├── tsconfig.node.json                # Node/Vite 侧 TS 配置
├── vite.config.ts                    # Vite 配置与开发代理
└── src/
    ├── api/
    │   ├── adapters/
    │   │   └── ReferenceAdapters.ts  # submit-meta 旧/新结构适配与 API payload 映射
    │   ├── fixtures/
    │   │   └── ReferenceData.ts      # 前端参考单源 fixture：meta、目录、详情、评测记录
    │   ├── AgentService.ts           # 提交/预检查/评测记录服务，默认 mock，可切 live
    │   ├── DatasetService.ts         # 目录/详情服务，默认 mock，可切 live
    │   └── MockApiUtils.ts           # mock envelope、延迟、失败注入工具
    ├── components/
    │   ├── common/
    │   │   └── PageHeroCard.vue      # 通用页面头图/统计卡
    │   ├── dataset/
    │   │   ├── DatasetCategorySection.vue   # 数据集列表页分类分区
    │   │   ├── DatasetFilterBar.vue         # 数据集列表页分类筛选条
    │   │   ├── DatasetMediaGallery.vue      # 数据集详情页媒体展示
    │   │   └── DatasetSubcategoryCard.vue   # 数据集卡片
    │   ├── dialog/
    │   │   ├── ConfirmDialog.vue     # 通用确认弹窗
    │   │   └── LoginDialog.vue       # 登录弹窗
    │   ├── icon/
    │   │   └── AppIcon.vue           # 应用图标组件
    │   ├── navigation/
    │   │   ├── NavBar.vue            # 顶部导航
    │   │   └── UserSidebar.vue       # 用户中心侧边栏
    │   └── submit/
    │       ├── SubmitActionBar.vue         # 提交操作栏与错误/警告展示
    │       ├── SubmitBasicInfoForm.vue     # 智能体基础信息表单
    │       ├── SubmitDatasetPanel.vue      # 提交页数据集树、空态、刷新态、错误态
    │       ├── SubmitMethodSelector.vue    # API / Docker 提交方式切换
    │       ├── SubmitParameterControls.vue # 新版参数控件：滑条+数字输入+超时警示
    │       └── SubmitVisibilityCard.vue    # 是否公开到排行榜
    ├── composables/
    │   └── useSubmitDatasetCatalog.ts # 提交页专用目录加载、缓存、状态机
    ├── layouts/
    │   ├── PublicLayout.vue          # 公共页面布局
    │   └── UserLayout.vue            # 登录后页面布局
    ├── router/
    │   ├── modules/
    │   │   ├── LegacyRoutes.ts       # 历史路径重定向
    │   │   ├── PublicRoutes.ts       # 公共页面路由
    │   │   └── UserRoutes.ts         # 需登录页面路由
    │   ├── index.ts                  # 路由实例
    │   ├── RouteGuards.ts            # 登录态守卫
    │   ├── RouteMeta.d.ts            # 路由 meta 类型扩展
    │   └── RouteNames.ts             # 路由名与跳转对象
    ├── store/
    │   ├── DatasetCatalogStore.ts    # 公开数据集页/详情页目录 store
    │   ├── SubmitDraftStore.ts       # 提交页草稿、展开分组、持久化与目录同步
    │   └── UserStore.ts              # 用户状态、登录注册、资料、头像、回跳
    ├── styles/
    │   ├── LayoutShared.css          # 布局共享样式
    │   ├── primitives.css            # 基础原子样式
    │   ├── semantic.css              # 语义层样式
    │   └── tokens.css                # 设计 token
    ├── types/
    │   ├── AgentTypes.ts             # 提交/评测相关类型
    │   ├── CommonTypes.ts            # 通用 envelope / persisted state 类型
    │   └── DatasetTypes.ts           # 数据集目录/详情类型
    ├── utils/
    │   ├── DatasetUtils.ts           # 数据集展示、选择、格式化工具
    │   ├── request.ts                # axios 请求封装与 envelope 适配
    │   ├── StorageUtils.ts           # localStorage 持久化工具
    │   ├── SubmitParameterUtils.ts   # 参数归一化、步长校验、软提示
    │   └── SubmitValidation.ts       # 提交 payload 校验
    ├── views/
    │   ├── ContactUs.vue             # 联系我们页面
    │   ├── DatasetCatalogPage.vue    # 数据集目录页
    │   ├── DatasetDetail.vue         # 数据集详情页
    │   ├── EvaluationReport.vue      # 评测详情页
    │   ├── HomePage.vue              # 首页
    │   ├── LeaderboardPage.vue       # 排行榜页
    │   ├── ProfilePage.vue           # 用户资料页
    │   ├── SubmitAgentPage.vue       # 唯一提交页
    │   └── UserCenter.vue            # 用户中心评测记录页
    ├── App.vue                       # 应用根组件
    └── main.ts                       # 应用启动、Pinia、路由、401 处理
```
