# goldenwave Roadmap

## v0.1 — Standard & Skeleton（当前）
建立"标准"认知。
- [x] SPEC.md 五层架构标准
- [x] L1–L5 分层规范 + governance
- [x] init.sh 一键生成骨架
- [x] Skills: goldenwave-init / knowledge / profile
- [x] templates: knowledge + profile

## v0.2 — Governed Ingest（建立壁垒）
从"模板"跃迁为"系统"。设计见 [docs/v0.2-router-PRD.md](docs/v0.2-router-PRD.md)。
- [x] 半自动摄入路由器 skill：`skills/goldenwave-ingest`（inbox → 判断 事实/知识/人格 → 人确认）
- [x] `_pending/` 草稿区约定（低置信/敏感项安全阀）
- [ ] facet 半衰期 + 四态生命周期（借 OpenHuman PROFILE.md）
- [ ] 证据分级落地到摄入流水线（capture→score→render→inject）
- [ ] 实测：投 10 条混合原料，路由准确率 ≥ 80%、敏感项 0 直接入库

## v0.3+ — Distill & Connect（吸引贡献者）
- [ ] 三合一蒸馏冷启动：微信 / IM / 历史文档（借 immortal 采集器，注意 GNU 兼容）
- [ ] MCP server：把个人库暴露给任意 agent（借 Pieces）
- [ ] 被动 connector：账号定时 auto-fetch
- [ ] L4 人格实例 + Agent Loop 自迭代

## 设计红线（任何版本不破）
1. 一切皆 markdown + git，可 diff 可审计
2. 本地优先，云为可选
3. 事实 / 知识 / 人格三维分层不混淆
4. 标准写进库，不绑定任何单一工具
