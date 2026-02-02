# git规范

## important

- 不要上传main！！！
  - main 受保护：禁止直接 push，只能 PR(dev→main)
  - dev 受保护：禁止直接 push，只能 PR 合并(feature→dev)
  - 个人分支可自由 push
- 多更新同步
- 建立个人开发分支

## 仓库说明

- main分支为主分支，保存稳定版本，平时不要更改任何内容
- dev为开发分支，确认代码无bug后便可合并，合并时如遇冲突及时解决，注意不要改动远程dev仓库，尽量改动本地代码
- 在本地或者远程仓库新建个人开发分支（命名建议feature/xxx），便于调试和存档，功能实现后先同步到远程开发分支，同步成功后，再提交pull request与远程dev分支合并。
  - 这样可以减少与远程dev的冲突，避免误操作修改现有代码
  - 注意更新，本地dev一定要与远程dev保持一致，避免代码落后版本过多
  - 本地代码可以多同步至个人开发分支，如实现一个模块或小功能，便于调试、回溯等等
- 任何合并都要写详细的提交信息，如实现的功能、改bug等等
- 在dev实现阶段任务后将同步至main分支
- share文件夹为共享文件夹，可以把任务分配、to-do list、临时详细、共享资料等等放在里面，但是不要放大文件

## 处理流

以下处理流依据git命令行，实际IDE可能不需要输入命令，供参考

### 准备工作

#### git config

设置用户名和邮箱，与github保持一致  
该步骤在IDE中可能不需要

```shell
git config --global user.name "JToday666"
git config --global user.email 1154362900@qq.com
```

#### 仓库创建

克隆仓库到本地

```shell
git clone https://github.com/JToday666/agent_security_platform.git
```

切换到dev分支

```shell
git checkout dev
```

或者用一条命令

```shell
git clone -b dev https://github.com/JToday666/agent_security_platform.git
```

### 提交信息规范

建议标准：

- feat: ... 新功能
- fix: ... 修 bug
- docs: ... 文档
- refactor: ... 重构不改行为
- chore: ... 杂项（依赖、脚手架）

> ***一个 commit 只做一件事***（不混改）。

### 协作工作流

#### step1：创建功能分支（可选）

```shell
git branch <branch_name>
git checkout <branch_name>
```

或者

```shell
git checkout -b <branch_name>
```

#### step2：开发

开发

#### step3：暂存

将更改的内容暂存

```shell
git add ......(file)
```

#### step4：提交

将暂存区的内容提交至本地仓库

```shell
git commit -m ....(message)
```

#### step5：拉取/同步dev

在合并前保持本地dev与远程仓库一致

```shell
git pull origin dev
```

#### step6：推送/同步

从本地仓库推送至远程仓库

```shell
git push origin feature/xxx
```

#### step7：合并分支

合并feature与dev

> 注意，**该命令是将其他分支的修改合并到当前分支**

合并时要先签出到目标分支，即dev

```shell
git checkout dev
```

合并有多种方式：merge（合并）、squash（压缩）、rebase（变基）  

```shell
git merge --squash feature/xxx
git commit -m "......"
```

个人分支 PR 到 dev 时用 Squash（一条提交对应一个功能/修复，历史干净）

#### step8：提交PR

在开发完当前功能后，提交pull request，将feature分支合并到dev分支

提 PR：feature/xxx → dev（推荐 Squash merge）

#### step9：解决冲突

如果遇到冲突，不要强制替换

- 同步最新dev
- 本地切换到功能分支
- 将dev合并到feature
- 解决冲突
- 提交合并结果
- 推送更新到远程feature
- 返回PR

解决冲突后，PR界面应该会自动更新，可以正常合并

> **关键点：**
>
> - 在feature合并dev分支，避免直接操作受保护分支
> - 避免强制推送
> - 验证代码，运行测试确保冲突解决，未引入新问题

#### step10：删除

PR 合并后删分支：本地/远端都删（保持仓库干净）

## 其他

## 总结

- 给你一份「小团队最小可用」的 main + dev 规范分支约定
  - main：稳定/可发布（受保护，禁止直接 push）
  - dev：日常集成（受保护，禁止直接 push；只能 PR 合并）
  - feature/<topic_xxx>：功能分支（从 dev 拉）
  - fix/<topic_xxx>：普通修复（从 dev 拉）
  - hotfix/<topic_xxx>：线上紧急修复（从 main 拉）
- 标准工作流（功能开发）
  - 同步 dev：git checkout dev && git pull --rebase origin dev
  - 拉功能分支：git checkout -b feature/xxx
  - 开发提交：git add ... && git commit -m "feat: ..."
  - 推送远端分支：git push -u origin feature/xxx
  - 提 PR：feature/xxx → dev（推荐 Squash merge）
  - PR 合并后删分支：本地/远端都删（保持仓库干净）
- 发版工作流（dev → main）
  - 从 dev 提 PR 到 main：dev → main
  - 合并后打 tag：vX.Y.Z
  - 写 Release Notes（可选但强烈建议）
- 热修复（main 出事）
  - git checkout main && git pull origin main
  - git checkout -b hotfix/xxx
  - 修复并提交，推送，提 PR：hotfix/xxx → main
  - main 合并后：把同样修复合回 dev（PR 或 cherry-pick）
- 提交信息
  - 采用 Conventional Commits：feat/fix/docs/refactor/chore + 简短描
  - 例：fix: handle null user in login
- 仓库卫生
  - 必备：.gitignore、README.md
  - 产物/临时文件禁止入库；share/docs 只放可版本化内容
