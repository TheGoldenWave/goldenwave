# Phase 0：Repo Scorecard Metadata 必须与 Raw Evidence 分离

## 结论

Phase 0 人工代理 baseline 的 repo 侧证据只能保存 allowlist metadata；原始响应、reviewer 文字说明、工具轨迹和任何可能含私有正文的内容必须留在 `.private/` 或 `ephemeral`。

## 原因

`run_id` preflight 只能证明 suite 已确认且批次集合合法，不能阻止后续 scorecard 把私有路径、自由文本、二次回答记录或多余字段写入 Git。只要 repo scorecard 允许自由扩展，P0-06 的“原始输出不入库”边界就会失效。

## 通用规则

1. repo scorecard 顶层只允许固定 allowlist 字段。
2. 嵌套结构也要固定键名和枚举，不能留自由文本口袋。
3. `evidence_refs` 必须是 opaque ID，不能是 `.private/` 路径、URI 或点前缀引用。
4. 单响应人工基线必须显式记录 `first_response_turns=1` 与 `reviewer_reframes=0`，否则按 invalid run 处理。
5. YAML 解析必须禁用 alias 和重复键，避免隐式结构绕过 schema。

## 来源

- `tests/specs/phase0/real-dogfood-README.md`
- `tests/specs/phase0/p0-baseline-preflight.rb`
- `tests/specs/phase0/p0-scorecard-metadata-validate.rb`
- `docs/prd/goldenwave-strategy/.artifacts/p0-06-qa.md`
