# L5 — Git 规范（审计层）

> 一切产物纳入 git：版本、留痕、回滚、跨设备同步。这是 goldenwave 对黑盒记忆的根本差异。

## 约定
- 整个个人库是一个 git 仓（profile / wiki / .kb / inbox 都在内）。
- 提交信息用受控前缀：`feat / ingest / update / archive / lint / fix / chore`。
- `.kb/log.md` 记录所有 agent 操作（人类可读的时间轴）。

## 跨设备同步
- 通过 git remote（GitHub/GitLab/自建）同步，借 Hermes 式 ssh-over-443 绕网络限制。
- 个人库走个人远端；公司/团队库走团队远端，物理隔离。
- 路径用环境变量 `$KB_ROOT`，不硬编码绝对路径（跨 Mac/Windows）。

## 敏感数据与 git
- L3 数据入库前，按 governance：或 `.gitignore` 排除、或转私有/加密仓。
- 凭据永不入库（见 L1 硬规则）。
