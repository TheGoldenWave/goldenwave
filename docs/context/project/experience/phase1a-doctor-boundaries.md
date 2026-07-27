# Phase 1A Doctor 边界经验

## 结论

安全诊断器必须把外部输入路径、正文读取范围和 Git 仓归属分别收紧，不能因为操作名是“只读”就默认没有泄露面。

## 可复用规则

1. manifest/template 中的路径先与冻结 allowlist 精确比对，再做任何文件访问。
2. 元数据诊断只读取首段 frontmatter；不要为一个字段加载完整正文。
3. 库内 symlink 一律 fail closed，结果只返回库内相对路径，不返回指向目标。
4. `git rev-parse --show-toplevel` 必须与目标根精确一致；位于父 Git 仓中不代表目标自身已初始化。
5. `.private/` 与 `.ephemeral/` 不仅要被 ignore，还要检查是否已经被强制跟踪。
6. 真实库只读演练使用运行前后元数据与 Git 状态指纹证明无副作用。

## 来源

- `skills/goldenwave-init/scripts/gw_init/doctor.py`
- `skills/goldenwave-init/scripts/gw_init/renderer.py`
- `tests/specs/goldenwave-init/security-regression.spec.rb`
