---
name: goldenwave-init
description: 安全初始化一个符合 GoldenWave Phase 1A 合同的本地 Knowledge Base。适用于“初始化 goldenwave / 新建个人知识库 / 创建 GoldenWave Knowledge Base”这类请求。
---

# goldenwave-init

把 GoldenWave Knowledge Base 初始化为 `gwkb/v0.1`，先计划、再确认、后写入，最后做只读 doctor 校验。

## 执行方式
1. 询问目标路径。默认值可用 `~/KnowledgeBase`。
2. 定位当前 Skill 自身目录，再调用该目录下的 bundled 脚本：
   `python3.11 <skill_dir>/scripts/goldenwave_init.py ...`
3. 先运行：
   `plan --target <PATH> --mode new --format json`
4. 向用户展示 plan 结果，只在用户明确确认后继续。
5. 再运行：
   `apply --target <PATH> --mode new --git off|init --format json`
6. apply 成功后立刻运行：
   `doctor --target <PATH> --format json`
7. 只根据 JSON 结果解释下一步，不要自己补写模板文件、个人事实、commit、remote 或 push。

## 规则
- `plan` 必须是只读；若目标非空、危险或冲突，停止并返回冲突。
- 默认使用 `--git off`；只有用户明确要求时才用 `--git init`。
- 不自动填写 `profile/console/me.md`，不猜测任何个人事实。
- 不自动执行 `git add`、`git commit`、`git remote`、`git push`。
- 使用脚本返回的 JSON envelope 判断成功、阻塞或失败，不解析装饰性文本。
