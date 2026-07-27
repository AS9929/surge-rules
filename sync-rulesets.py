#!/usr/bin/env python3
"""自托管 Surge RULE-SET：从上游合并 + 保留 owned，并写回 conf 引用。

用法（私有仓）:
  python3 scripts/config/sync-rulesets.py
  python3 scripts/config/sync-rulesets.py --apply
  python3 scripts/config/sync-rulesets.py --apply --no-fetch

用法（公开仓 AS9929/surge-rules，脚本与 config.yaml 同目录）:
  python3 sync-rulesets.py
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def _detect_roots() -> tuple[Path, Path, list[Path]]:
    """返回 (workspace, rulesets_dir, conf_files)。公开仓时 rulesets=仓根。"""
    script = Path(__file__).resolve()
    # 私有仓: scripts/config/sync-rulesets.py
    private_ws = script.parents[2]
    private_rs = private_ws / "configs" / "rulesets"
    if (private_rs / "config.yaml").is_file():
        return (
            private_ws,
            private_rs,
            [
                private_ws / "configs" / "blankmagic.conf",
                private_ws / "configs" / "surfboard.conf",
            ],
        )
    # 公开仓: sync-rulesets.py 与 config.yaml 同级
    public_rs = script.parent
    if (public_rs / "config.yaml").is_file():
        return public_rs, public_rs, []
    raise SystemExit(f"找不到 config.yaml（tried {private_rs} and {public_rs}）")


WORKSPACE, RULESETS, CONF_FILES = _detect_roots()
OWNED = RULESETS / "owned"
CONFIG_PATH = RULESETS / "config.yaml"

MARKER_BEGIN = "# --- managed-rulesets:begin ---"
MARKER_END = "# --- managed-rulesets:end ---"


def load_config() -> dict:
    if yaml is None:
        raise SystemExit("需要 PyYAML: pip3 install pyyaml")
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def ruleset_defs(cfg: dict) -> list[dict]:
    items = cfg.get("rulesets")
    if not items:
        raise SystemExit("config.yaml 缺少 rulesets: 列表")
    return items


def fetch_url(url: str, timeout: int = 60) -> str:
    try:
        r = subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout), url],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
        err = (r.stderr or "").strip() or f"curl exit {r.returncode}"
        raise RuntimeError(err)
    except FileNotFoundError:
        pass
    req = urllib.request.Request(url, headers={"User-Agent": "vps-infra-sync-rulesets/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalize_line(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if s.startswith("- "):
        s = s[2:].strip()
    # skip clash YAML keys
    if s.endswith(":") and "," not in s:
        return None
    if s.startswith("payload:"):
        return None
    return s


def is_denied(line: str, denylist: list[str]) -> bool:
    low = line.lower()
    return any(d.lower() in low for d in denylist)


def parse_rules(text: str, denylist: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = normalize_line(raw)
        if not line or is_denied(line, denylist):
            continue
        # Must look like a Surge/Clash rule
        if not re.match(
            r"^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR6?|IP-ASN|PROCESS-NAME|URL-REGEX|USER-AGENT|AND|OR|RULE-SET)\b",
            line,
            re.I,
        ):
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out


def item_relpath(item: dict) -> str:
    """成品相对 configs/rulesets/ 的路径；默认 {id}.list，可用 path: 覆盖。"""
    rel = (item.get("path") or f"{item['id']}.list").lstrip("/")
    return rel


def read_owned(item: dict) -> list[str]:
    path = OWNED / item_relpath(item)
    if not path.exists():
        return []
    return parse_rules(path.read_text(encoding="utf-8"), denylist=[])


def merge_list(item: dict, cfg: dict, fetch: bool) -> Path:
    name = item["id"]
    rel = item_relpath(item)
    use_deny = bool(item.get("apply_denylist"))
    denylist = list(cfg.get("denylist") or []) if use_deny else []
    skip_kw = [k.lower() for k in (item.get("skip_keywords") or [])]
    owned = read_owned(item)
    generated: list[str] = []
    seen = {x.lower() for x in owned}

    if fetch:
        for url in item.get("upstream") or []:
            try:
                text = fetch_url(url)
                print(f"  ✓ fetch {name}: {url}")
            except Exception as e:
                print(f"  ✗ fetch {name}: {url} ({e})", file=sys.stderr)
                continue
            for line in parse_rules(text, denylist):
                key = line.lower()
                if key in seen:
                    continue
                if skip_kw and any(k in key for k in skip_kw):
                    continue
                seen.add(key)
                generated.append(line)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# {rel} — 自托管 Surge RULE-SET",
        f"# Generated: {now}",
        f"# Owned: configs/rulesets/owned/{rel} (optional)",
        "# Do not edit GENERATED by hand; re-run sync-rulesets.py",
        "",
        "# ===== OWNED =====",
        *owned,
        "",
        "# ===== GENERATED =====",
        *generated,
        "",
    ]
    out = RULESETS / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  → wrote {out.relative_to(WORKSPACE)} (owned={len(owned)} generated={len(generated)})")
    return out


def resolve_base_url(cfg: dict) -> str:
    base = (cfg.get("base_url") or "local").strip()
    if base in ("local", "file"):
        return str(RULESETS.resolve())
    return base.rstrip("/")


def ruleset_ref(base: str, item: dict) -> str:
    rel = item_relpath(item)
    if base.startswith("/") or base.startswith("file:"):
        return str(Path(base.replace("file://", "")) / rel)
    return f"{base}/{rel}"


def policy_for(item: dict, surfboard: bool) -> str:
    if surfboard and item.get("policy_surfboard"):
        return item["policy_surfboard"]
    return item["policy"]


def build_managed_block(cfg: dict, surge_style: bool) -> str:
    base = resolve_base_url(cfg)
    lines = [
        MARKER_BEGIN,
        "# 由 scripts/config/sync-rulesets.py --apply 生成；正文在 configs/rulesets/",
        "# 源: https://github.com/AS9929/surge-rules",
    ]
    for item in ruleset_defs(cfg):
        name = item["id"]
        policy = policy_for(item, surfboard=not surge_style)
        url = ruleset_ref(base, item)
        lines.append(f"# {item.get('comment', name)}")
        for inline in item.get("prepend_inline") or []:
            lines.append(inline)
        opts = []
        if surge_style:
            opts.append('"update-interval=86400"')
            matching = item.get("matching") or "extended-matching"
            opts.append(matching)
            extra = item.get("surge_options")
            if extra:
                opts.append(extra)
            lines.append(f"RULE-SET,{url},{policy}," + ",".join(opts))
        else:
            extra = item.get("surfboard_options")
            if extra:
                lines.append(f"RULE-SET,{url},{policy},{extra}")
            else:
                lines.append(f"RULE-SET,{url},{policy}")
    lines.append(MARKER_END)
    return "\n".join(lines)


def apply_to_conf(path: Path, cfg: dict) -> None:
    text = path.read_text(encoding="utf-8")
    surge_style = path.name == "blankmagic.conf"
    block = build_managed_block(cfg, surge_style=surge_style)
    footer_key = "surge" if surge_style else "surfboard"
    footer = (cfg.get("footer") or {}).get(footer_key, "").rstrip() + "\n"
    new_text = replace_rule_section(text, block, footer)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"  → applied {path.relative_to(WORKSPACE)}")
    else:
        print(f"  · unchanged {path.relative_to(WORKSPACE)}")


def replace_rule_section(text: str, managed_block: str, footer: str) -> str:
    """用 managed RULE-SET + footer 替换整个 [Rule] 段正文。"""
    lines = text.splitlines(keepends=True)
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == "[Rule]":
            start = i
            continue
        if start is not None and end is None:
            # 下一 section
            if line.startswith("[") and line.strip().endswith("]") and line.strip() != "[Rule]":
                end = i
                break
    if start is None:
        raise SystemExit("conf 中未找到 [Rule] 段")
    if end is None:
        end = len(lines)

    out = lines[: start + 1]
    out.append(managed_block + "\n")
    if footer:
        out.append(footer if footer.endswith("\n") else footer + "\n")
    out.extend(lines[end:])
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync & apply self-hosted Surge rulesets")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="不拉上游；与 --apply 同用时只改 conf",
    )
    args = ap.parse_args()

    cfg = load_config()
    items = ruleset_defs(cfg)
    print("━━━ sync rulesets ━━━")
    print(f"  base_url = {resolve_base_url(cfg)}")
    print(f"  lists = {len(items)}")

    if args.no_fetch and args.apply:
        print("  skip list rebuild (--apply --no-fetch)")
    else:
        for item in items:
            merge_list(item, cfg, fetch=not args.no_fetch)

    if args.apply:
        print("━━━ apply to conf ━━━")
        for conf in CONF_FILES:
            if conf.exists():
                apply_to_conf(conf, cfg)
            else:
                print(f"  skip missing {conf}")
    else:
        print("提示: 加 --apply 可更新 blankmagic.conf / surfboard.conf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
