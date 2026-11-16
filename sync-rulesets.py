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
            [private_ws / "scripts" / "config" / "templates" / "surge.conf"],
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


class UpstreamError(RuntimeError):
    """任一上游拉取失败/为空：整批不写，避免用残缺内容覆盖 GENERATED。"""


def domain_key(rule: str) -> tuple[str, str]:
    """读取规则的域名类型和目标，供上游规则集过滤使用。"""
    kind, _, fields = rule.lower().partition(",")
    return kind, fields.split(",", 1)[0].strip().rstrip(".")


def parse_domainset(text: str) -> list[str]:
    """将 DOMAIN-SET 转为同义域名规则，保留前导点表示的后缀匹配。

    不接受 URL、IP 或未知格式，避免把上游错误页静默转换成可发布规则。
    """
    rules = []
    for raw in text.splitlines():
        host = normalize_line(raw)
        if host is None:
            continue
        suffix = host.startswith(".")
        host = host.lstrip(".").lower()
        if not re.fullmatch(r"[a-z0-9_-]+(?:\.[a-z0-9_-]+)+", host):
            raise ValueError(f"Invalid DOMAIN-SET entry: {raw[:100]}")
        kind = "DOMAIN-SUFFIX" if suffix else "DOMAIN"
        rules.append(f"{kind},{host}")
    return rules


def build_list(item: dict, cfg: dict) -> tuple[str, list[str], list[str]]:
    """拉上游并与 owned 合并，返回 (relpath, owned, generated)；失败抛 UpstreamError。"""
    name = item["id"]
    rel = item_relpath(item)
    use_deny = bool(item.get("apply_denylist"))
    denylist = list(cfg.get("denylist") or []) if use_deny else []
    skip_kw = [k.lower() for k in (item.get("skip_keywords") or [])]
    exceptions = [
        domain_key(line)
        for source in (item.get("skip_domains_from_owned") or [])
        for line in read_owned({"id": source})
    ]
    skip_exact = {host for kind, host in exceptions if kind == "domain"}
    skip_suffix = {host for kind, host in exceptions if kind == "domain-suffix"}
    owned = read_owned(item)
    generated: list[str] = []
    seen = {x.lower() for x in owned}

    for url in item.get("upstream") or []:
        try:
            text = fetch_url(url)
            if item.get("upstream_format") == "domainset":
                text = "\n".join(parse_domainset(text))
        except Exception as e:
            raise UpstreamError(f"{name}: {url} ({e})") from e
        rules = parse_rules(text, denylist)
        if not rules:
            raise UpstreamError(f"{name}: {url} (no parsable rules; HTML/error page?)")
        print(f"  ✓ fetch {name}: {url} ({len(rules)} rules)")
        for line in rules:
            key = line.lower()
            if key in seen:
                continue
            if skip_kw and any(k in key for k in skip_kw):
                continue
            if skip_exact or skip_suffix:
                kind, host = domain_key(key)
                if kind in {"domain", "domain-suffix"} and (
                    host in skip_exact
                    or any(host == suffix or host.endswith("." + suffix) for suffix in skip_suffix)
                ):
                    continue
            seen.add(key)
            generated.append(line)
    return rel, owned, generated


GENERATED_PREFIX = "# Generated: "


def render_list(rel: str, owned: list[str], generated: list[str], stamp: str) -> str:
    lines = [
        f"# {rel} — 自托管 Surge RULE-SET",
        f"{GENERATED_PREFIX}{stamp}",
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
    return "\n".join(lines) + "\n"


def _without_stamp(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith(GENERATED_PREFIX))


def write_list(rel: str, owned: list[str], generated: list[str]) -> bool:
    """内容未变时保留原时间戳且不写盘，返回是否写入。"""
    out = RULESETS / rel
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = render_list(rel, owned, generated, stamp)
    if out.exists() and _without_stamp(out.read_text(encoding="utf-8")) == _without_stamp(content):
        print(f"  · unchanged {out.relative_to(WORKSPACE)}")
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"  → wrote {out.relative_to(WORKSPACE)} (owned={len(owned)} generated={len(generated)})")
    return True


def rebuild_lists(items: list[dict], cfg: dict) -> int:
    results = []
    for item in items:
        try:
            results.append(build_list(item, cfg))
        except UpstreamError as e:
            print(f"  ✗ fetch {e}", file=sys.stderr)
            print("✗ 上游拉取失败：本次不写任何 list（避免 GENERATED 被清空）", file=sys.stderr)
            return 1
    for rel, owned, generated in results:
        write_list(rel, owned, generated)
    return 0


def validate_lists(items: list[dict]) -> int:
    """--no-fetch：只检查成品 list 是否存在、GENERATED 是否为空，不改文件。"""
    missing = 0
    for item in items:
        rel = item_relpath(item)
        path = RULESETS / rel
        if not path.exists():
            print(f"  ✗ missing {path.relative_to(WORKSPACE)}", file=sys.stderr)
            missing += 1
            continue
        text = path.read_text(encoding="utf-8")
        generated = text.split("# ===== GENERATED =====", 1)[-1] if "# ===== GENERATED =====" in text else ""
        count = len(parse_rules(generated, denylist=[]))
        flag = "  ⚠ GENERATED 为空" if item.get("upstream") and count == 0 else ""
        print(f"  · {rel}: owned={len(read_owned(item))} generated={count}{flag}")
    return 1 if missing else 0


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


def build_managed_block(cfg: dict) -> str:
    base = resolve_base_url(cfg)
    lines = [
        MARKER_BEGIN,
        "# 由 scripts/config/sync-rulesets.py --apply 生成；正文在 configs/rulesets/",
        "# 源: https://github.com/AS9929/surge-rules",
    ]
    for item in ruleset_defs(cfg):
        url = ruleset_ref(base, item)
        lines.append(f"# {item.get('comment', item['id'])}")
        for inline in item.get("prepend_inline") or []:
            lines.append(inline)
        opts = ['"update-interval=86400"', item.get("matching") or "extended-matching"]
        if item.get("surge_options"):
            opts.append(item["surge_options"])
        lines.append(f"RULE-SET,{url},{item['policy']}," + ",".join(opts))
    lines.append(MARKER_END)
    return "\n".join(lines)


def apply_to_conf(path: Path, cfg: dict) -> None:
    text = path.read_text(encoding="utf-8")
    block = build_managed_block(cfg)
    footer = (cfg.get("footer") or {}).get("surge", "").rstrip() + "\n"
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
        help="不拉上游、不重建 list（只校验成品）；与 --apply 同用时只改 conf",
    )
    args = ap.parse_args()

    cfg = load_config()
    items = ruleset_defs(cfg)
    print("━━━ sync rulesets ━━━")
    print(f"  base_url = {resolve_base_url(cfg)}")
    print(f"  lists = {len(items)}")

    if args.no_fetch:
        print("  skip list rebuild (--no-fetch)")
        rc = validate_lists(items)
    else:
        rc = rebuild_lists(items, cfg)
    if rc:
        return rc

    if args.apply:
        print("━━━ apply to conf ━━━")
        for conf in CONF_FILES:
            if conf.exists():
                apply_to_conf(conf, cfg)
            else:
                print(f"  skip missing {conf}")
    else:
        print("提示: 加 --apply 可更新 Surge 模板；之后运行 make regen 生成新批次")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
