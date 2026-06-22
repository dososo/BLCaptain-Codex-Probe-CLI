# `/status` 样本库

这些样本用于验证 BLCaptain Codex Probe CLI 对不同 Codex `/status` 形态的解析能力。所有样本均为脱敏或合成数据，不包含真实会话 ID、cookie、token 或系统凭据。

| 文件 | 场景 | 预期动作 |
|---|---|---|
| `codex-desktop-healthy.txt` | 上下文、5 小时额度和 7 天额度都健康 | 继续 |
| `codex-desktop-context-near-limit.txt` | 当前上下文偏重，但短窗口和周额度仍健康 | 降配 |
| `codex-desktop-weekly-low.txt` | 7 天额度偏低 | 停止 |
| `english-fast-mode.txt` | 英文 `/status`，高推理模式且 5 小时额度偏低 | 降配 |

样本库的目标不是替代官方 dashboard，而是让解析规则、报告决策和 README 示例都能被本地复现。
