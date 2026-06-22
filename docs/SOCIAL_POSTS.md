# 社媒短文

## X

我做了一个本地小工具：BLCaptain Codex Probe CLI。

它不是替代官方 dashboard，也不碰登录态。

你把 Codex `/status` 贴给 Codex，让它调用本地 CLI，就能得到一份报告：

- 为什么这次任务贵
- 怎么降配
- 什么时候该停
- Skill / 输出有没有 AI 味、插件风险和敏感信息

最适合长会话、重度 Codex 用户、内容创作者和轻开发交付。

开源：  
https://github.com/dososo/BLCaptain-Codex-Probe-CLI

## 小红书

标题备选：

- 我做了个 Codex 用量体检工具：告诉你什么时候该停
- Codex 越聊越贵？我做了个本地分析 CLI
- 把 `/status` 贴给 Codex，让它告诉你为什么贵

正文：

最近我自己用 Codex 做项目时，最明显的感觉不是「不会提示词」，而是会话越来越长以后，很难判断：

- 这次到底为什么贵？
- 是不是该换小模型？
- 该继续做，还是先停下来开新会话？
- Skill / 输出是不是 AI 味太重，或者带了不该有的插件风险？

所以我做了一个本地工具：**BLCaptain Codex Probe CLI**。

它的用法不是让普通用户背命令，而是直接在 Codex 桌面版里说一句：

> 这是我的 Codex /status。请先脱敏，然后用 BLCaptain Codex Probe CLI 生成用量报告，告诉我为什么贵、怎么降配、什么时候该停。

它会生成一份本地 Markdown 报告，分析当前会话 token、额度风险、停止线，也能体检 Skill / 输出里的 AI 味、插件风险和敏感信息。

边界我也写得很死：

- 不登录 OpenAI
- 不读浏览器 cookie
- 不碰 token 和系统凭据
- 不上传云端
- 不承诺省钱或无限额度

它更像一个「Codex 使用刹车片」：不是帮你绕过限制，而是提醒你别在长会话里无意识烧上下文。

适合重度 Codex 用户、内容创作者、轻开发交付和经常写 Skill / README / 代码的人。

GitHub 已开源：  
https://github.com/dososo/BLCaptain-Codex-Probe-CLI

评论区可以把你最常见的 Codex 用量焦虑发我，我继续补规则。
