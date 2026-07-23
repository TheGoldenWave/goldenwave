# goldenwave Roadmap

## 接口战略

GoldenWave 优先 CLI 化，MCP 后置。CLI 是标准、Contract 与 governed ingest 的首要执行面；它必须先证明本地初始化、验证、摄入、诊断和迁移可以确定性运行。MCP 在 CLI 命令合同、权限边界和 validator 稳定后再开放，用于让 Agent 读取正式知识或提交受治理候选，不另写一套业务逻辑。

Malow 的接口顺序与此互补：Malow 优先提供 Project-scoped MCP 集成面，CLI 只承担诊断、显式导入和启动 MCP。GoldenWave CLI、后续 GoldenWave MCP 与 Malow Adapter 共同遵守版本化 Contract，但不要求两个项目锁步发布。

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
- [ ] 发布 `knowledge-patch/v0.1.0`：JSON Schema、合法/非法示例、validator、兼容说明与 Malow 契约测试向量
- [ ] 建立 `goldenwave` CLI 统一入口，首批命令为 `init / validate / ingest / doctor`
- [ ] CLI 与 Skill / script 复用同一 Contract、validator 和摄入服务，不通过 shell 拼接复制领域规则
- [ ] CLI 验收：临时 Knowledge Base 可重复初始化，合法/非法 envelope 可确定性验证，重复 ingest 幂等，`doctor` 能定位目录、版本与权限问题
- [ ] facet 半衰期 + 四态生命周期（借 OpenHuman PROFILE.md）
- [ ] 证据分级落地到摄入流水线（capture→score→render→inject）
- [ ] 实测：投 10 条混合原料，路由准确率 ≥ 80%、敏感项 0 直接入库

## v0.3+ — Distill & Connect（吸引贡献者）
- [ ] 三合一蒸馏冷启动：微信 / IM / 历史文档（借 immortal 采集器，注意 GNU 兼容）
- [ ] CLI 与 Contract 稳定后提供 MCP server：先开放只读检索，再开放写入 Inbox 候选；不允许绕过 route / confirm 直接修改正式知识
- [ ] 被动 connector：账号定时 auto-fetch
- [ ] L4 人格实例 + Agent Loop 自迭代

## 设计红线（任何版本不破）
1. 正式知识保持 Markdown + Git；L3 envelope / Schema 等中间协议保持文本化、可 diff、可审计
2. 本地优先，云为可选
3. 事实 / 知识 / 人格三维分层不混淆
4. 标准写进库，不绑定任何单一工具
