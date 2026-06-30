# L1 — Profile 规范（事实层）

> 存「关于我此刻为真的事实」，含人格描述。与 L2 Knowledge 严格分离。

## 目录
```
profile/
├── console/
│   ├── me.md             # 主上下文：人生阶段/年度目标/绝对禁止清单/操舵原则
│   └── agent-contract.md # 隐私分级 + 访问矩阵 + 行为偏好
├── persona/              # 人格描述（源）
│   ├── index.md  expression-dna.md  traits.md  decision-style.md  voice-samples.md
├── 01-body-health/  02-finance/  03-consumption/  04-social/  05-time-energy/
├── 06-digital-legal/  07-spatial/  08-skills/  09-career-assets/
└── INDEX.md  kb-schema.md
```

## 九大事实域
| 域 | 内容 | 默认敏感度 | 维护者 |
|---|---|---|---|
| 01 body-health | 尺码/生理/过敏/病史/用药 | L3 | hybrid |
| 02 finance | 资产配置/现金流/订阅 | L3 | agent |
| 03 consumption | 品牌黑白名单/设备耗材/愿望单 | L1 | hybrid |
| 04 social | 亲友档案/职场关键人/人情账 | L3 | human |
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

## 硬规则
1. 绝不存凭据（密码/私钥/完整卡号）；只存"实体关联指针"。
2. L3 数据必带 `verified`；agent 引用过期 L3 须声明截止日。
