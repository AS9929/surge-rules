# surge-rules

Self-hosted Surge / Surfboard RULE-SET lists.

Maintained from private infra via `sync-rulesets.py` / `publish-rulesets.sh`.

## Subscribe

Base: `https://raw.githubusercontent.com/AS9929/surge-rules/main/<name>.list`

| File | Purpose | Typical policy |
|------|---------|----------------|
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
