# 公共页面与共享 UI 说明

本文档说明 `src/modules/public/` 与 `src/shared/ui/` 的职责边界，以及共享 UI 的分类与使用原则。

## 1. 公共页面模块

`src/modules/public/` 承担无需登录即可访问的页面。

### 1.1 页面文件

| 文件                              | 职责                                                       |
| --------------------------------- | ---------------------------------------------------------- |
| `pages/HomePage.vue`              | 首页，展示平台入口、流程引导、登录入口与已登录用户快捷入口 |
| `pages/ContactPage.vue`           | 联系方式页面                                               |
| `pages/LeaderboardPage.vue`       | 排行榜页面入口                                             |
| `pages/NotFoundPage.vue`          | 404 页面                                                   |
| `components/HomeWorkflowCard.vue` | 首页流程卡片，展示四步引导                                 |

### 1.2 HomePage 的重点逻辑

首页不仅是静态展示页，还承担几个应用入口职责：

- 根据 `isLogin` 决定按钮跳向“提交评测 / 查看记录”还是“登录 / 联系我们”
- 通过 `userStore.openLoginDialog()` 直接唤起登录弹窗
- 提供退出登录确认框
- 用打字机效果逐步呈现标题和副标题

它是“公共区入口”和“已登录用户工作台快捷入口”的结合点。

## 2. 共享 UI 的定位

`src/shared/ui/` 的目标不是提供通用样式片段，而是提供可在多个模块复用的业务无关组件。

当前按用途分为六类：

### 2.1 actions

| 文件                   | 职责                                                         |
| ---------------------- | ------------------------------------------------------------ |
| `actions/UiButton.vue` | 统一按钮组件，兼容普通按钮、链接按钮、加载态、块级模式等能力 |

适用场景：

- 页面主操作按钮
- 跳转按钮
- 带 loading / disabled 语义的统一操作按钮

### 2.2 branding

| 文件                     | 职责                |
| ------------------------ | ------------------- |
| `branding/AppIcon.vue`   | 对 Iconify 的薄封装 |
| `branding/BrandLogo.vue` | 品牌 Logo 组件      |

适用场景：

- 导航栏
- 首页 Hero
- 反馈提示或空态图标

### 2.3 display

| 文件                     | 职责                             |
| ------------------------ | -------------------------------- |
| `display/MetricCard.vue` | 指标卡片                         |
| `display/StatusTag.vue`  | 评测状态标签，结合状态规则做展示 |
| `display/UiTag.vue`      | 基础标签组件                     |

适用场景：

- 详情页指标区
- 列表状态展示
- 页面局部标签展示

### 2.4 feedback

| 文件                         | 职责                               |
| ---------------------------- | ---------------------------------- |
| `feedback/ConfirmDialog.vue` | 通用确认弹窗                       |
| `feedback/InlineNotice.vue`  | 行内提示                           |
| `feedback/PageStateCard.vue` | 统一的加载 / 空态 / 错误态页面卡片 |

适用场景：

- 提交确认
- 错误提示
- 页面加载态、空态和失败态

### 2.5 forms

| 文件                          | 职责                                       |
| ----------------------------- | ------------------------------------------ |
| `forms/FormField.vue`         | 统一字段壳，提供 label、help、错误区与插槽 |
| `forms/UiChoiceCardGroup.vue` | 卡片式选项组                               |
| `forms/UiToggleField.vue`     | 布尔开关字段                               |

适用场景：

- 登录 / 注册表单
- 提交评测表单
- 个人资料表单

### 2.6 page

| 文件                    | 职责             |
| ----------------------- | ---------------- |
| `page/PageHeroCard.vue` | 页面头部 Hero 卡 |
| `page/SectionCard.vue`  | 通用内容分区卡   |

适用场景：

- 各业务页面头部
- 详情页、表单页、列表页内容分区

## 3. 共享 UI 使用边界

共享 UI 组件应满足以下条件才适合放入 `src/shared/ui/`：

- 至少能被两个模块复用，或明显属于跨模块基础组件
- 不依赖某个业务模块的私有状态结构
- 输入输出稳定，职责明确

反例：

- 只在数据集目录页使用的数据集卡片
- 只在提交页使用的提交方式选择器

这些组件应继续留在各自模块的 `components/` 内。

## 4. 为什么不在这里展开样式细节

共享 UI 文档当前只写：

- 组件用途
- 典型输入输出
- 使用边界

不展开每个样式实现细节，原因是：

- 样式属于实现层，变化频率高
- 当前任务的核心目标是帮助开发者理解结构和调用关系，而不是复刻视觉实现

如果后续需要补充组件级 props / emits 手册，应单独追加专题文档，而不是把本文件扩成样式大全。

## 5. 与 app 样式体系的关系

共享 UI 的视觉基础并不写死在组件内部，而是建立在 `src/app/styles/` 的全局样式体系之上。

关系大致如下：

```text
tokens.scss -> primitives.scss -> semantic.scss -> layout-shared.scss / utilities.scss
-> shared/ui 组件
-> 模块页面与模块组件
```

因此要理解一个共享 UI 组件的最终表现，通常需要同时查看：

- 组件本身
- `src/app/styles/semantic.scss`
- `src/app/styles/tokens.scss`
