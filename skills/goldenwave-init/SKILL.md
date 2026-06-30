---
name: goldenwave-init
description: 初始化一个 goldenwave 个人 AI 操作系统知识库（L1 Profile + L2 Knowledge + L5 Git 骨架）。当用户说"初始化 goldenwave / 新建个人知识库 / 搭个人操作系统"时触发。
---

# goldenwave-init

初始化一个符合 goldenwave SPEC 的个人库。

## 步骤
1. 询问目标路径（默认 `~/KnowledgeBase`）。
2. 运行 `bash scripts/init.sh <路径>` 生成骨架：
   - `wiki/`（8 类页面目录 + INDEX/kb-schema/glossary）
   - `profile/`（console + 9 域 + persona + INDEX/kb-schema）
   - `.kb/`（log.md + scripts）、`inbox/`、`.sources/`
   - `CLAUDE.md`（agent 工作约定）、`.gitignore`、`sync.sh`
3. `git init` 并首次提交。
4. 引导用户填 `profile/console/me.md` 三要素（人生阶段/年度目标/绝对禁止清单）。
5. 提示把 `skills/` 挂到 agent。

## 原则
遵循 SPEC.md 与 spec/*.md。事实进 L1、知识进 L2、人格描述进 persona、人格实例进 L4。
