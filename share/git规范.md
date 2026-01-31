# git规范

## important

- 不要上传main！！！
- 多更新同步

## 仓库说明

- main分支为主分支，保存稳定版本，平时不要更改任何内容
- dev为开发分支，确认代码无bug后便可合并，合并时如遇冲突及时解决，注意不要改动远程dev仓库，尽量改动本地代码
- 建议在本地仓库新建个人开发分支（命名建议feature_xxx），便于调试和存档，功能实现后先与本地dev合并，合并成功后，再提交pull request与远程dev分支合并。
  - 这样可以减少与远程dev的冲突，避免误操作修改现有代码
  - 注意更新，本地dev一定要与远程dev保持一致，避免代码落后版本过多
  - 本地代码可以多同步至个人开发分支，如实现一个模块或小功能，便于调试、回溯等等
- 任何合并都要写详细的提交信息，如实现的功能、改bug等等
- 在dev实现阶段任务后将同步至main分支
- share文件夹为共享文件夹，可以把任务分配、to-do list、临时详细、共享资料等等放在里面

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

### 协作工作流

#### step1：创建功能分支

```shell
git branch <branch_name>
git checkout <branch_name>
```

或者

```shell
git checkout -b <branch_name>
```

#### step2：开发

开发 - 暂存 - 提交  
至本地开发分支
