# surge-rules

Self-hosted Surge / Surfboard RULE-SET lists.

Upstream sources are merged daily by GitHub Actions (`Daily Sync Upstream`).
Hand-tuned rules live in `owned/` (copied from private infra on publish).

## Subscribe

Base: `https://raw.githubusercontent.com/AS9929/surge-rules/main/<path>`

Custom lists: `custom/`.

| File | Purpose | Typical policy |
|------|---------|----------------|
| `custom/direct.list` | `自定义直连` | `DIRECT` |
| `custom/proxies.list` | `自定义代理` | `Proxies` |
| `custom/japan.list` | `自定义日本（Nodeseek）` | `日本` |
| `custom/reject.list` | `自定义拒绝` | `REJECT` |
| `custom/reject-nodrop.list` | `自定义 REJECT-NO-DROP（QUIC / TG 转圈）` | `REJECT-NO-DROP` |
| `custom/no-hybrid.list` | `NO-HYBRID（招行等）` | `NO-HYBRID` |
| `custom/ext-update.list` | `外部资源更新提示` | `Final` |
| `reject.list` | `AdBlock / reject` | `REJECT` |
| `claude.list` | `Claude / Anthropic` | `Claude` |
| `chatgpt.list` | `ChatGPT / OpenAI` | `Chatgpt` |
| `gemini.list` | `Gemini` | `Gemini` |
| `ai-misc.list` | `其它 AI 兜底` | `Proxies` |
| `youtube.list` | `YouTube` | `Youtube` |
| `netflix.list` | `Netflix` | `Netflix` |
| `truthsocial.list` | `Truth Social` | `TruthSocial` |
| `whatsapp.list` | `WhatsApp` | `Whatsapp` |
| `twitter.list` | `Twitter / X` | `Twitter` |
| `telegram.list` | `Telegram` | `Telegram` |
| `bahamut.list` | `Bahamut` | `Bahamut` |
| `apple.list` | `Apple` | `Apple` |
| `china.list` | `China DIRECT` | `DIRECT` |
| `global.list` | `Global Proxy` | `Proxies` |

### Surge example

```ini
RULE-SET,https://raw.githubusercontent.com/AS9929/surge-rules/main/reject.list,REJECT,"update-interval=86400",pre-matching
RULE-SET,https://raw.githubusercontent.com/AS9929/surge-rules/main/claude.list,Claude,"update-interval=86400",extended-matching
RULE-SET,https://raw.githubusercontent.com/AS9929/surge-rules/main/chatgpt.list,Chatgpt,"update-interval=86400",extended-matching
RULE-SET,https://raw.githubusercontent.com/AS9929/surge-rules/main/custom/direct.list,DIRECT,"update-interval=86400",extended-matching
```

jsDelivr: `https://cdn.jsdelivr.net/gh/AS9929/surge-rules@main/<path>`

## Daily sync

Workflow: `.github/workflows/daily-sync.yml` — every day 00:00 CST.

Manual: Actions → **Daily Sync Upstream** → Run workflow.

## License

Aggregated from public community sources plus local owned rules. Use at your own risk.
