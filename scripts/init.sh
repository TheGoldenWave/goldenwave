#!/bin/bash
# goldenwave init — 生成符合 SPEC 的个人 AI 操作系统骨架
# 用法: bash init.sh [目标路径]   (默认 ~/KnowledgeBase)
set -euo pipefail
KB="${1:-$HOME/KnowledgeBase}"
TODAY="$(date '+%Y-%m-%d')"
echo "🌊 goldenwave init → $KB"

if [ -e "$KB" ] && [ -n "$(ls -A "$KB" 2>/dev/null || true)" ]; then
  echo "⚠️  $KB 已存在且非空，仅补缺失目录，不覆盖已有文件。"
fi

# --- 目录骨架 ---
mkdir -p "$KB"/wiki/{concepts,entities,methods,guides,projects,syntheses,comparisons,insights}
mkdir -p "$KB"/profile/{console,persona,01-body-health,02-finance,03-consumption,04-social,05-time-energy,06-digital-legal,07-spatial,08-skills,09-career-assets}
mkdir -p "$KB"/{inbox,.sources/research-reports,.kb/scripts}

# --- 安全写：文件存在则跳过 ---
w() { local f="$1"; shift; if [ -f "$f" ]; then echo "  skip $f"; else cat > "$f"; echo "  +    $f"; fi; }

w "$KB/INDEX.md" <<EOF
---
title: 知识库索引
updated: $TODAY
---
# 个人知识库
- [结构化知识 wiki/](wiki/index.md)
- [个人事实档案 profile/](profile/INDEX.md)
EOF

w "$KB/wiki/index.md" <<EOF
---
title: 结构化知识总览
updated: $TODAY
---
# Knowledge
按 type 浏览：concepts / entities / methods / guides / projects / syntheses / comparisons / insights
EOF

for t in concepts entities methods guides projects syntheses comparisons insights; do
  w "$KB/wiki/$t/index.md" <<EOF
---
title: $t 索引
updated: $TODAY
---
# $t
EOF
done

w "$KB/profile/INDEX.md" <<EOF
---
title: Profile 个人事实档案索引
updated: $TODAY
---
# Profile
- 控制台: [me.md](console/me.md) · [agent-contract.md](console/agent-contract.md)
- 人格域: [persona/](persona/index.md)
- 九大事实域: 01-body-health … 09-career-assets
EOF

w "$KB/profile/console/me.md" <<EOF
---
id: me
domain: console
title: 个人主上下文
sensitivity: L1
maintainer: human
refresh: 90d
verified: $TODAY
---
# 个人主上下文
## 当前人生阶段
（待填）
## 年度三大目标
1. （待填）
## 绝对禁止清单
- （待填）
## 操舵原则（取舍优先级）
（待填）
EOF

w "$KB/.kb/log.md" <<EOF
# 操作日志
## [$TODAY] init | goldenwave 骨架生成
EOF

w "$KB/CLAUDE.md" <<EOF
# Agent 工作约定（goldenwave）
本库遵循 goldenwave SPEC。事实进 profile/(L1)、知识进 wiki/(L2)、人格描述进 profile/persona、人格实例属 Project(L4)。
一切 markdown + git 可审计。新建页面必须合规 frontmatter。
EOF

w "$KB/.gitignore" <<EOF
.DS_Store
.obsidian/workspace*
EOF

w "$KB/sync.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
git add -A && git commit -m "${1:-chore: sync}" && git push 2>/dev/null || echo "提交完成（remote 未配置则跳过 push）"
EOF
chmod +x "$KB/sync.sh"

echo "✅ 骨架就绪。下一步："
echo "   1) cd $KB && git init && git add -A && git commit -m 'feat: goldenwave init'"
echo "   2) 填 profile/console/me.md 三要素"
echo "   3) 把 goldenwave/skills/ 挂到你的 agent"
