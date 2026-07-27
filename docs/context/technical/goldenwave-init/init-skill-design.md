---
feature_id: goldenwave-init
status: phase-1a-frozen
version: 0.1
updated: 2026-07-27
---

# GoldenWave Init Skill 技术设计

## 1. 设计结论

采用“薄 Skill + 自包含确定性初始化器 + doctor”的结构。初始化器是唯一执行事实源；Skill 只做自然语言适配，仓库根脚本只做向后兼容。未来统一 `goldenwave` CLI 必须复用同一内核，不能再实现一套模板生成逻辑。

本设计中的 init 专指最终用户 Knowledge Base 初始化。维护 GoldenWave 源码仓的 `.agents/skills/bootstrap-agentic-project` 属于开发基础设施，不进入用户级 init 的调用链。

## 2. 当前实现差距

| 现状 | 风险 | 目标 |
|------|------|------|
| Skill 使用相对路径调用仓库根脚本 | Skill 单独安装后失效 | 从 Skill 自身目录定位 bundled script |
| Bash heredoc 内嵌模板 | 模板漂移、跨平台弱 | 版本化 assets + Python 标准库渲染 |
| 非空目录仅补缺失文件 | 形成未知混合状态 | `new` 拒绝非空；`adopt` 独立规划 |
| 没有 manifest | 无法判断版本、归属和升级边界 | `.kb/goldenwave.json` |
| 没有 doctor | 生成成功不代表安全可用 | 结构、策略和 Git 行为验证 |
| `.private/` 未生成或 ignore | 违反当前 SPEC | 先生成安全规则，再允许 Git 操作 |
| `sync.sh` 尝试 add/commit/push | 权限和泄露边界过大 | init 不 push；同步由后续受管命令负责 |

## 3. 组件结构

```text
skills/goldenwave-init/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── goldenwave_init.py       # 命令入口和 JSON 输出
│   └── gw_init/                 # 可拆分的标准库模块
│       ├── planner.py
│       ├── renderer.py
│       ├── doctor.py
│       ├── git_policy.py
│       └── result.py
└── assets/
    └── kb-template/
        ├── template-manifest.json
        └── ...

scripts/init.sh                  # 兼容包装器，只转调上述入口
tests/specs/goldenwave-init/     # 验收 fixture 与集成测试
```

实现时遵守项目单文件规模约束；若入口超过约 300 行，按上图拆分模块。模板是输出资产，不把大段模板正文放入 `SKILL.md`。

## 4. 命令合同

### 4.1 Plan

```bash
python goldenwave_init.py plan \
  --target <path> \
  --mode new \
  --format json
```

约束：

- 不修改目标路径和 Git 状态。
- 对 target 做展开、规范化和真实路径边界检查。
- `new` 只接受不存在或为空的目标路径。
- 返回 `plan_id`、initializer version、target、actions、warnings、conflicts 和 Git 建议。
- apply 必须重新校验关键前置条件，不能盲信过期 plan。

### 4.2 Apply

```bash
python goldenwave_init.py apply \
  --target <path> \
  --mode new \
  --git off \
  --format json
```

约束：

- 在 target 同级创建权限受限的临时目录。
- 完整渲染模板、生成 manifest，并先对临时目录运行结构检查。
- 通过后原子 rename；若目标在 plan 后发生变化，返回冲突。
- Git 初始化在目标落位和 doctor 通过之后执行。
- `--git off` 完全不触碰 Git；任何模式都不配置 remote 或 push。

### 4.3 Doctor

```bash
python goldenwave_init.py doctor \
  --target <path> \
  --format json
```

结果结构沿用统一 envelope（见 4.5），`doctor` 只填充诊断相关字段。

```json
{
  "ok": false,
  "command": "doctor",
  "result_version": "gw-init/v1",
  "target": {
    "display_path": "~/KnowledgeBase",
    "root_token": "kb:2f4c6f5a1d8e"
  },
  "format_version": "gwkb/v0.1",
  "initializer_version": "0.1.0",
  "findings": [
    {
      "code": "GW_PRIVATE_TRACKED",
      "level": "unsafe",
      "severity": "error",
      "path": ".private/social/example.md",
      "message": "local_private file is tracked by Git"
    }
  ]
}
```

JSON 中不得包含文件正文、个人姓名或其他敏感内容。人类可读文本由同一结果对象渲染，避免两套判断逻辑。

### 4.4 Adopt Inventory

```bash
python goldenwave_init.py adopt inventory \
  --target <path> \
  --format json
```

约束：

- Phase 1A 的 `adopt inventory` 是只读盘点，不创建、修改、删除、rename、chmod、stage、commit 或 push 任何用户文件。
- 不在目标库内生成临时文件、锁文件、sidecar、cache 或迁移计划；结果只输出到 stdout/stderr。
- 允许的外部调用仅限只读文件系统遍历，以及 `git rev-parse`、`git check-ignore`、`git ls-files`、`git status --porcelain` 这类只读 Git 查询。
- 输出运行时诊断级别仅使用 `unsafe / invalid / repairable / advisory`，不把质量提示伪装成安全阻断。
- 只报告盘点事实与显式后续建议；不在 Phase 1A 引入自动修复、自动迁移或 candidate 生成。

### 4.5 稳定结果 Envelope

所有命令的 JSON 顶层结构固定如下：

```json
{
  "ok": true,
  "command": "plan",
  "result_version": "gw-init/v1",
  "initializer_version": "0.1.0",
  "format_version": "gwkb/v0.1",
  "target": {
    "display_path": "~/KnowledgeBase",
    "root_token": "kb:2f4c6f5a1d8e"
  },
  "summary": {
    "status": "ok",
    "message": "ready to apply"
  },
  "warnings": [],
  "conflicts": [],
  "findings": [],
  "artifacts": {}
}
```

固定规则：

- `result_version` 表示命令输出 envelope 版本，Phase 1A 冻结为 `gw-init/v1`。
- `format_version` 表示目标 Knowledge Base contract 版本；`plan` 对新建目标返回计划写入值，`doctor/adopt inventory` 对现有库返回检测到的值或 `null`。
- `target.display_path` 只暴露对人可读的脱敏路径；`target.root_token` 是基于 canonical root 的稳定 opaque token，用于跨日志关联。
- `summary.status` 仅使用 `ok / blocked / failed`；细粒度原因进入 `warnings`、`conflicts` 或 `findings`。
- `findings[*]` 固定包含 `code`、`level`、`severity`、`path`、`message`；其中 `level` 只允许 `unsafe / invalid / repairable / advisory`。
- `artifacts` 只放结构化元数据，例如 `plan_id`、`managed_template_count`、`git_mode`；不得塞入正文 diff、绝对临时路径或用户内容片段。

## 5. Manifest

`.kb/goldenwave.json` 建议包含：

```json
{
  "format_version": "gwkb/v0.1",
  "initializer_version": "0.1.0",
  "created_at": "2026-07-27T00:00:00Z",
  "managed_templates": {
    ".gitignore": "sha256:...",
    "AGENTS.md": "sha256:...",
    "CLAUDE.md": "sha256:...",
    "INDEX.md": "sha256:...",
    "kb-schema.md": "sha256:..."
  }
}
```

规则：

- `format_version` 在 Phase 1A 冻结为 `gwkb/v0.1`；`apply` 只写该值，`doctor` 对未知值返回 `GW_MANIFEST_INVALID`。
- Phase 1A 不引入 minor 自动兼容矩阵；除显式允许的 legacy 只读盘点外，运行时兼容规则是“已知且精确匹配”。
- checksum 只表示初始化器管理的模板基线，不把所有用户内容纳入 manifest。
- 用户修改过的受管文件在未来 upgrade 中生成 diff，不直接覆盖。
- `format_version` 对应 Knowledge Base contract；`initializer_version` 对应工具实现，二者不能混用。
- 时间使用带时区的 ISO 8601；测试通过注入 clock 保持可重复。

## 6. 模板策略

- 模板目录对应当前冻结的 Knowledge Base layout，不在脚本中用 heredoc 重复正文。
- 动态值只允许白名单变量，例如日期、format version 和库显示名。
- 使用简单、显式的替换器，不引入可执行模板语法。
- `template-manifest.json` 列出路径、类型、权限、动态变量和是否由 GoldenWave 管理。
- SPEC 变更顺序：先更新规范，再更新 template/doctor fixture，最后更新 Skill 行为说明。
- `AGENTS.md` 是跨 Agent 的规范入口；`CLAUDE.md` 使用普通桥接文件，避免 Windows symlink 差异。
- Phase 1A 的 managed template 清单冻结为：
  - 受管文件：`.gitignore`、`AGENTS.md`、`CLAUDE.md`、`INDEX.md`、`kb-schema.md`、`glossary.md`、`wiki/index.md`、`wiki/*/index.md`、`profile/INDEX.md`、`profile/kb-schema.md`、`profile/console/agent-contract.md`。
  - 创建后归用户管理：`profile/console/me.md`、`profile/persona/**`、九大事实域中的内容文件、`.kb/log.md`、`inbox/**`、`.sources/**`、`projects/**`、`.private/**`、`.ephemeral/**`。
- 目录存在性属于 layout contract，但只有受管文件进入 `managed_templates` checksum；空目录和用户内容不纳入 checksum。

## 7. 安全模型

### 7.1 路径安全

- 拒绝 `/`、用户主目录本身、GoldenWave 源码仓根和系统目录。
- 解析父目录真实路径，阻止 `..`、符号链接或 junction 越过批准目标。
- 不跟随目标内部未知 symlink 写文件。
- 临时目录使用操作系统安全 API 创建，权限遵循最小可见性。

### 7.2 Git 安全

- 在任何 add/commit 之前创建并验证 `.gitignore`。
- Phase 1A 冻结的默认 ignore 集为 `.private/`、`.ephemeral/`、`.DS_Store`、`Thumbs.db`；其中前两项属于安全 contract，后两项属于噪音抑制。
- doctor 使用 `git check-ignore` 验证 `.private/.gw-doctor-probe` 与 `.ephemeral/.gw-doctor-probe` 这两个 sentinel path。
- 使用 `git ls-files` 检测已跟踪的 local_private 文件；命中即 fail closed。
- init 不执行 remote、fetch、pull、push 或历史重写。
- 首次 commit 是独立的用户确认动作，不作为 apply 的隐式副作用。
- Phase 1A 将 `--git off` 冻结为默认值；只有用户显式选择时才执行 `git init`，且仍不自动 add/commit。

### 7.3 日志安全

- 本地操作日志记录动作类型、工具版本和 Knowledge Base 相对路径，不记录个人正文。
- `findings[*].path` 只允许返回 Knowledge Base 根下的相对路径；超出根路径的目标、symlink 指向和临时目录统一替换为 opaque token，例如 `outside://3f2c8d1a`、`temp://7ab42e11`。
- `target.display_path` 必须将用户 home 脱敏为 `~`（Windows 为 `%USERPROFILE%`）；除用户显式请求调试外，不在结果 JSON 中暴露 canonical absolute path。
- 错误堆栈默认不写入 Knowledge Base；调试模式也必须脱敏 target 之外的信息。
- 不启用网络遥测。

## 8. Doctor / Adopt Inventory 检查集

| 类别 | 检查 | 失败策略 |
|------|------|----------|
| Layout | 必需目录和文件存在 | error |
| Manifest | JSON 合法、版本可识别 | error |
| Frontmatter | 基础模板字段可解析 | error/warning，按文件类型定义 |
| Ignore | `.private/` 和 `.ephemeral/` 实际被忽略 | error |
| Git tracking | local_private 未被跟踪 | error |
| Paths | 无越界 symlink 或危险路径 | error |
| Permissions | 必需路径可读写，私有目录权限合理 | error/warning，按平台定义 |
| Drift | 受管模板 checksum 与基线差异 | warning，不自动覆盖 |
| Adopt inventory | 旧库结果分级为 `unsafe / invalid / repairable / advisory` | 仅报告，不修复 |

`validate` 与 `doctor` 后续可分层：`validate` 校验内容与 contract，`doctor` 检查运行环境、安全状态和跨文件不变量。MVP 可先由 doctor 覆盖初始化必需子集，但命令语义不得混淆。

## 9. 稳定错误码

首批建议：

| 错误码 | 含义 |
|--------|------|
| `GW_TARGET_UNSAFE` | 目标路径属于禁止范围 |
| `GW_TARGET_NOT_EMPTY` | `new` 模式目标非空 |
| `GW_TARGET_CHANGED` | plan 后目标状态发生变化 |
| `GW_RUNTIME_UNSUPPORTED` | Python 或平台能力低于冻结下限 |
| `GW_TEMPLATE_INVALID` | 模板或变量不合法 |
| `GW_APPLY_INCOMPLETE` | 原子落位前的生成或检查失败 |
| `GW_MANIFEST_INVALID` | manifest 缺失、损坏或版本未知 |
| `GW_PRIVATE_NOT_IGNORED` | local_private 未被 Git ignore |
| `GW_PRIVATE_TRACKED` | local_private 已进入 Git 索引 |
| `GW_EPHEMERAL_NOT_IGNORED` | ephemeral 路径未被 Git ignore |
| `GW_EPHEMERAL_FORMAL_PATH` | ephemeral 内容落入正式目录 |
| `GW_POLICY_DRIFT` | 旧库策略与冻结 contract 漂移 |
| `GW_GIT_UNAVAILABLE` | 用户请求 Git 但运行时不可用 |
| `GW_DOCTOR_FAILED` | doctor 存在未细分的阻塞 finding |

错误码一旦进入 fixture 即视为 experimental contract；修改需要兼容说明。

## 10. Skill 编排规则

1. 从 Skill 文件位置解析脚本路径，禁止假设当前目录是 GoldenWave 源码仓。
2. 先调用 `plan --format json`。
3. 无冲突时只对路径和 Git 选择做最小确认；存在 warning/conflict 时准确转述。
4. 用户批准后调用 apply，再无条件调用 doctor。
5. doctor 未通过时停止，不 commit，并给出与 finding 对应的修复建议。
6. doctor 通过后报告目标路径、format version 和下一步 onboarding。
7. Profile onboarding 使用 `goldenwave-profile` 或后续专用流程，不在 init 中猜测个人事实。

## 11. 测试策略

### 11.1 单元测试

- 路径规范化和危险路径拒绝；
- template manifest 解析和白名单变量；
- manifest checksum；
- JSON 结果与稳定错误码；
- doctor finding 聚合。

### 11.2 集成测试

- 不存在路径和空目录初始化；
- 同版本重复执行；
- 非空目录拒绝且零写入；
- plan 后目标变化；
- 路径含空格、中文和长路径；
- Git 不存在、未初始化和已初始化三种环境；
- `.private/` 未 ignore、已 ignore、已 tracked；
- `.ephemeral/` 未 ignore、误入正式目录；
- 渲染或 rename 中断后的清理；
- 无 Git identity 时不影响 apply/doctor；
- macOS、Linux、Windows 支持版本。

### 11.3 验收 fixture

在 `tests/specs/goldenwave-init/` 保存输入状态与预期 finding，不存真实个人数据。至少包含：

- `empty-target`；
- `existing-conflict`；
- `private-not-ignored`；
- `private-already-tracked`；
- `ephemeral-not-ignored`；
- `ephemeral-in-formal-path`；
- `manifest-unknown-version`；
- `managed-template-drift`；
- `path-traversal`。

## 12. 交付分段

### MVP-A：可靠新建

- 模板 assets、manifest、plan/apply；
- 空目录原子初始化；
- 人类可读与 JSON 输出；
- 幂等和冲突测试。

### MVP-B：可信门禁

- doctor、Git ignore/tracked 检查；
- 稳定错误码；
- 失败清理和跨平台测试。

### MVP-C：Skill 产品化

- 薄 Skill 编排；
- `agents/openai.yaml`；
- 根脚本兼容层；
- README Quick Start 和 sandbox dogfood。

### 后续：Adopt 与 Upgrade

- 已有库只读盘点；
- 迁移计划、备份与用户确认；
- 基于 manifest 的模板升级和 drift diff；
- 统一 `goldenwave` CLI 接入同一内核。

## 13. Phase 1A 冻结合同

### 13.1 Ephemeral 与 Ignore

1. Phase 1A 的规范 ephemeral 根目录冻结为 Knowledge Base 根下的 `.ephemeral/`。
2. `.ephemeral/` 只用于原始聊天、临时导入材料和处理中间产物；`wiki/`、`profile/`、`projects/`、`inbox/`、`.sources/`、`.kb/` 都不是合法的 ephemeral 落点。
3. `.gitignore` 的安全必选规则冻结为 `.private/` 与 `.ephemeral/`；缺失任一规则时 `doctor` 与 `adopt inventory` 都按 `unsafe` fail closed。

### 13.2 `format_version`

1. Phase 1A 新建库写入的 `format_version` 冻结为 `gwkb/v0.1`。
2. `initializer_version` 使用独立 semver，表示工具实现版本，不得替代或推断 `format_version`。
3. `doctor` 对 Phase 1A 管理库只接受精确匹配的 `gwkb/v0.1`；未知值、空值或损坏值返回 `GW_MANIFEST_INVALID`。
4. `adopt inventory` 可在只读模式下报告 legacy 或未知版本，但结果级别是 `invalid` 或 `repairable`，不触发写入迁移。

### 13.3 Python 与 Windows 降级

1. 最低运行时冻结为 Python `3.11`。
2. 低于 `3.11` 时所有命令立即返回 `GW_RUNTIME_UNSUPPORTED`，不做部分执行。
3. Windows 平台若无法可靠证明目标路径和每个父级组件未经过 symlink/junction 越界，则返回 `GW_TARGET_UNSAFE`；不以“尽力而为”继续写入。
4. Windows 上无法收紧 POSIX 权限位不构成单独阻断；隐私边界仍以路径校验、`.gitignore` 和 Git 门禁为主，但必须把权限能力缺口报告为 warning。

### 13.4 Git 默认

1. `apply` 的默认 Git 策略冻结为 `--git off`。
2. 用户显式选择后才允许执行 `git init`；即便如此也不自动 `git add`、`commit`、配置 remote 或 push。
3. `doctor` 未通过时禁止任何 Git 写操作建议被渲染为默认下一步。

### 13.5 Managed Template 边界

1. `managed_templates` 的 Phase 1A 清单固定为第 6 节列出的受管文件集合。
2. 这些文件允许在未来 `upgrade` 中做 checksum drift 检查，但 Phase 1A 不自动覆盖用户改动。
3. 所有用户事实、日志、来源、候选、私有正文和 ephemeral 内容在创建后立即归用户管理，不进入 `managed_templates`。

### 13.6 `adopt inventory` 只读合同

1. `adopt inventory` 是已有库盘点入口，不是迁移器，也不是 repair 模式。
2. 它只输出分级诊断、风险摘要和后续建议，不生成 candidate、不写 manifest、不补模板、不改 `.gitignore`。
3. 运行时必须在 dirty worktree、存在外部自动化和已有 Git 历史的情况下保持幂等且只读。

### 13.7 路径脱敏合同

1. 对用户展示的目标路径使用 `target.display_path`；home 目录脱敏为 `~` 或 `%USERPROFILE%`。
2. 对目标根内文件使用相对路径；对根外路径、临时目录和 symlink 指向使用 opaque token。
3. 任何结果、日志或错误都不得包含文件正文、远端 URL、用户名或 target 之外的绝对路径。
