# 三端策略组图标 · v1

统一用于 Surge、SurgeLike iOS、SurgeLike Mac 的配置图标，客户端代码不参与。

- 品牌徽章：32 单位画布、30 单位浅灰底片、8 单位圆角、21 单位品牌图形。
- 功能图标：透明背景、统一蓝色与 1.9 单位线宽；通用 AI 使用星簇。
- 客户端使用 256×256 透明 PNG；同名 SVG 为可复现的矢量成品。
- 国家旗帜及 AI 节点的图灵头像沿用现有素材，只在统一映射中登记。
- `sources/` 保留固定版本的上游 SVG；来源和许可记录在 `sources.json`。
  Lobe Icons 为 MIT，Simple Icons 与所用 SVG Repo 图形为 CC0；品牌标识权利归各持有人。
  TruthSocial 的简化 T 字标及功能符号由本项目绘制，不冒称上游原图。

离线重新生成：

```sh
python3 scripts/config/build-group-icons.py
```

需要已有的 `rsvg-convert` 或可用的 CairoSVG，不会下载或安装依赖。
改变素材后先检查深浅背景预览，再发布整个图标目录，最后更新
`configs/client-platforms.yaml` 的 `policy_group_icons` 为新发布提交的固定 URL。

`make rulesets-publish` 会同步此目录；生成器只按映射更新 `[Proxy Group]` 的
`icon-url`，不改变分组名称、顺序、成员、节点或分流规则。
