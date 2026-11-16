# surge-rules

Self-hosted Surge RULE-SET lists. Daily sync from private `AS9929/surge-rulesets`.

Base: `https://raw.githubusercontent.com/AS9929/surge-rules/main/<path>`

| File | Purpose | Policy |
|------|---------|--------|
| `apple.list` | `Apple` | `Apple` |
| `custom/direct.list` | `自定义直连` | `DIRECT` |
| `custom/proxies.list` | `自定义代理` | `Proxies` |
| `custom/japan.list` | `自定义日本（Nodeseek）` | `日本` |
| `custom/reject.list` | `自定义拒绝（由 AdBlock 控制）` | `AdBlock` |
| `custom/protocol-reject.list` | `特定域名 UDP 协议控制（保持既有拒绝）` | `REJECT` |
| `custom/reject-nodrop.list` | `自定义 REJECT-NO-DROP（QUIC / TG 转圈）` | `REJECT-NO-DROP` |
| `custom/no-hybrid.list` | `NO-HYBRID（招行等）` | `NO-HYBRID` |
| `custom/ext-update.list` | `外部资源更新提示` | `Final` |
| `reject.list` | `AdBlock / reject` | `AdBlock` |
| `claude.list` | `Claude / Anthropic` | `Claude` |
| `chatgpt.list` | `ChatGPT / OpenAI` | `Chatgpt` |
| `gemini.list` | `Gemini` | `Gemini` |
| `grok.list` | `Grok / xAI` | `Grok` |
| `cursor.list` | `Cursor` | `Cursor` |
| `meta-ai.list` | `Meta AI` | `Meta AI` |
| `ai-misc.list` | `通用 AI（其余 AI 服务）` | `通用 AI` |
| `speedtest.list` | `Speedtest` | `Speedtest` |
| `discord.list` | `Discord` | `Discord` |
| `youtube.list` | `YouTube` | `Youtube` |
| `netflix.list` | `Netflix` | `Netflix` |
| `truthsocial.list` | `Truth Social` | `TruthSocial` |
| `whatsapp.list` | `WhatsApp` | `Whatsapp` |
| `twitter.list` | `Twitter / X` | `Twitter` |
| `telegram.list` | `Telegram` | `Telegram` |
| `bahamut.list` | `Bahamut` | `Bahamut` |
| `github.list` | `GitHub` | `GitHub` |
| `google.list` | `Google` | `Google` |
| `microsoft.list` | `Microsoft` | `Microsoft` |
| `china.list` | `China（由 CN 控制）` | `CN` |
| `global.list` | `Global Proxy` | `Proxies` |

jsDelivr: `https://cdn.jsdelivr.net/gh/AS9929/surge-rules@main/<path>`

## AI service routing

Separate lists: `claude.list`, `chatgpt.list`, `gemini.list`, `grok.list`, `cursor.list`, `meta-ai.list`.

`ai-misc.list` covers the remaining AI services, including Copilot. Bind it to a dedicated general AI policy.
