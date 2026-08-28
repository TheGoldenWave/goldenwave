# L1 — Profile 规范（事实层）

> 存「关于我及与我有关的当前事实」，含人格描述与用户中心社交关系。与 L2 Knowledge 严格分离。

## 目录
```
profile/
├── console/
│   ├── me.md             # 主上下文：人生阶段/年度目标/绝对禁止清单/操舵原则
│   └── agent-contract.md # 隐私分级 + 访问矩阵 + 行为偏好
├── persona/              # 人格描述（源）
│   ├── index.md  expression-dna.md  traits.md  decision-style.md  voice-samples.md
├── 01-body-health/  02-finance/  03-consumption/
├── 04-social/             # Social Memory 安全索引与 git_tracked 摘要
│   ├── people/  collectives/  relationships/
│   └── affiliations/  interactions/  commitments/
├── 05-time-energy/
├── 06-digital-legal/  07-spatial/  08-skills/  09-career-assets/
└── INDEX.md  kb-schema.md
```

## 九大事实域
| 域 | 内容 | 默认敏感度 | 维护者 |
|---|---|---|---|
| 01 body-health | 尺码/生理/过敏/病史/用药 | L3 | hybrid |
| 02 finance | 资产配置/现金流/订阅 | L3 | agent |
| 03 consumption | 品牌黑白名单/设备耗材/愿望单 | L1 | hybrid |
| 04 social | 人/组织关系、互动、承诺与关系维护上下文 | L3 | human |
| 05 time-energy | 生物钟/能量小偷/充电方式 | L1 | human |
| 06 digital-legal | 数字身份指针/订阅合约/保单摘要 | L3 | hybrid |
| 07 spatial | 常驻地参数/高频点/通勤载具 | L2 | human |
| 08 skills | 硬技能栈/软实力/已有自动化 | L1 | human |
| 09 career-assets | 核心卖点/STAR案例/数据背书 | L2 | hybrid |

## 字段哲学（区别于 Knowledge）
- 用 `verified`（最后核验日）+ `refresh`（核验周期）取代 wiki 的 `updated`。
- `sensitivity`: L0/L1/L2/L3；`maintainer`: human/agent/hybrid。
- facet 半衰期：人格按年（365d），订阅/渠道按周。

## persona 子域
人格描述进此（L2 起步，语料样本 L3，refresh 365d，maintainer hybrid）。
人格**实例**（可运行副本）不进这里，属 L4 Project。详见判定口诀。

## 04-social — Social Memory

### 定位

Social Memory 是以 `self` 为唯一锚点的个人社交图谱，目标是帮助用户维护真实关系。它不等于联系人列表、企业 CRM、组织知识库或第三方人格画像。

### 六类对象

| kind | 含义 | 核心约束 |
|---|---|---|
| `person` | 与我有关的具体人 | 不凭同名、同公司或同群聊自动合并 |
| `collective` | 家庭、圈子、团队、公司、社群或 household | 只存与我有关的组织关系上下文 |
| `relationship` | `self` 与一个 Person/Collective 的关系边 | 必须且只能有一个端点为 `self` |
| `affiliation` | Person→Collective 或 Collective→Collective 的关联 | 不替代我与该 Party 的 relationship |
| `interaction` | 一次有意义的互动事件 | 追加式；至少关联一个 Person/Collective |
| `commitment` | 用户需要履行的后续动作 | 必须有 owner、状态与到期规则 |

`Party` 是 `Person | Collective` 的抽象类型，不单独落盘；`self` 不复制为普通 Person。

### 公共字段

Social Memory 对象必须包含：

```yaml
id: per_01...                 # 按 kind 使用 opaque 前缀 + ULID
kind: person
record_status: active         # active|inactive|archived|redacted|revoked
sensitivity: L3
policy_tags: [third_party]
storage_class: local_private  # git_tracked|local_private|ephemeral
authorization:
  scopes: [store, summarize]
  basis: self_context
  retention_until: null
  revoked_at: null
verified: 2026-07-23
refresh: 90d
confidence: 1.0
source_refs: []
related: []
```

对象 ID 与文件名默认不含姓名。显示名只能出现在其存储等级允许的正文或 frontmatter 中。

### 不变量

1. V1 不保存与 `self` 无关的孤立 Party，也不建模任意第三方之间的完整社交图谱。
2. Interaction 是事件依据，Relationship 是当前摘要；不得通过改写事件美化关系历史。
3. 推断不能直接成为事实。`inference` 必须进入 `_pending/`，用户确认后仍保留证据等级。
4. 第三方敏感事实缺少来源、授权范围或核验日期时不得进入正式层。
5. 身份合并只生成候选，必须由用户确认，并保留可回滚引用映射。
6. 撤回对象不得继续参与查询、简报、建议、导出或自动重建。
7. `record_status` 表示记录生命周期；Commitment 的业务进度必须另用 `commitment_status`，不得复用公共状态字段。

### 存储映射

- `profile/04-social/`：逻辑入口、安全索引和用户明确允许 Git 跟踪的摘要。
- `.private/social/`：默认 Social Memory 正文；逻辑上仍属 L1，但不进入任何 Git 历史。
- `inbox/_pending/social/`：未确认对象、关系、推断、合并和权限候选。
- 原始聊天默认 `ephemeral`，处理后清理；用户明确保留时也必须重新选择授权、保留期与存储等级。
- 同一逻辑对象只能有一个 canonical storage，索引不得复制高敏正文。

## 硬规则
1. 绝不存凭据（密码/私钥/完整卡号）；只存"实体关联指针"。
2. L3 数据必带 `verified`；agent 引用过期 L3 须声明截止日。
3. Social Memory 默认 `sensitivity: L3`、`storage_class: local_private`、`maintainer: human`。
4. 不保存可操纵性标签、脆弱点清单、关系价值分或未经授权的敏感人格推断。
