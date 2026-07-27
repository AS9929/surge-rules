# surge-rules

Self-hosted Surge / Surfboard RULE-SET lists.

Maintained from private infra via `sync-rulesets.py` / `publish-rulesets.sh`.

## Subscribe

Base: `https://raw.githubusercontent.com/AS9929/surge-rules/main/<name>.list`

| File | Purpose | Typical policy |
|------|---------|----------------|
| `custom-direct.list` | `自定义直连` | `DIRECT` |
| `custom-proxies.list` | `自定义代理` | `Proxies` |
| `custom-japan.list` | `自定义日本（Nodeseek）` | `日本` |
| `custom-reject.list` | `自定义拒绝` | `REJECT` |
| `custom-reject-nodrop.list` | `自定义 REJECT-NO-DROP（QUIC / TG 转圈）` | `REJECT-NO-DROP` |
| `custom-no-hybrid.list` | `NO-HYBRID（招行等）` | `NO-HYBRID` |
| `ext-update.list` | `外部资源更新提示` | `Final` |
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
# ... see blankmagic.conf managed-rulesets block
```

jsDelivr: `https://cdn.jsdelivr.net/gh/AS9929/surge-rules@main/<name>.list`

## License

Aggregated from public community sources plus local owned rules. Use at your own risk.
