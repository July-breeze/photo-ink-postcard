# Photo Ink Postcard

一个可复用的 Codex Skill：把用户自己的风景、人物或动物摄影制作成自适应摄影水墨明信片。横向与方形照片输出 3:4 竖版上下双区，竖向照片输出 4:3 横版左右双区；实拍确定性保留，水墨区采用东方留白与减法重构。最后由脚本完成版式、文字与像素完整性校验。

> 本仓库不包含训练照片或私人摄影作品。随包附带的水墨图均为虚构、非特定地点的通用参考资产。

## 效果原则

- 实拍区不进行生成式重绘、补景或调色。
- 每张卡片继承原照片纵横比；两个视觉区尺寸完全一致。
- 4:3 照片保持 4:3，不用模糊条带强行扩充为 16:9。
- 竖向照片自动切换为 2048 × 1536 px 横版，左实拍、右水墨；英文仍以整张画布水平居中置底。
- 插画区采用偏置边角构图、大片定向留白、局部消隐和少量书写性笔触。
- 明确主体人物作为小尺度叙事焦点保留；偶然游客、远处人群与杂物删除。
- 明确主体动物保留数量、姿态和朝向，但压缩为少量墨形；环境最多保留两三个大形体。
- 输出为 1536 × 2048 px 竖版或 2048 × 1536 px 横版、PNG、300 dpi。
- 标题使用真实手写字体，副标题使用小号无衬线字体。

## 仓库结构

```text
photo-ink-postcard-github/
├── .agents/plugins/marketplace.json
├── plugins/photo-ink-postcard/
│   ├── plugin.json
│   └── skills/photo-ink-postcard/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── assets/
│       │   ├── style-material-reference.png
│       │   ├── composition-horizontal-water.png
│       │   ├── composition-human-landscape.png
│       │   ├── composition-mountain-diagonal.png
│       │   ├── composition-small-focal-point.png
│       │   └── composition-layered-forest.png
│       ├── references/
│       │   ├── prompt-template.md
│       │   └── style-routing.md
│       └── scripts/
│           ├── check_environment.py
│           ├── compose_postcard.py
│           └── verify_postcard.py
├── requirements.txt
└── LICENSE
```

## 环境要求

- Codex 或支持 Agent Skills / Plugins 的兼容环境。
- 可用的图像生成能力；Skill 会用它生成独立水墨面板。
- Python 3.10 或更高版本。
- Pillow 10 或更高版本。
- 一款真实英文手写字体。Windows 默认会尝试 French Script MT、Segoe Script 和 Lucida Handwriting；macOS 与 Linux 也包含常见候选。未找到时可通过 `--title-font` 指定字体文件。

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

检查环境：

```bash
python plugins/photo-ink-postcard/skills/photo-ink-postcard/scripts/check_environment.py
```

## 安装方式一：作为 GitHub Marketplace 安装

仓库推送到 GitHub 后，将下面的 `OWNER/REPO` 替换为真实地址：

```bash
codex plugin marketplace add OWNER/REPO
```

然后重启 ChatGPT 桌面端或 Codex，打开 Plugins Directory，选择 **Photo Ink Postcard** 来源并安装插件。

升级仓库版本后，可刷新 Marketplace：

```bash
codex plugin marketplace upgrade photo-ink-postcard-marketplace
```

## 安装方式二：只安装 Skill

如果不需要 Marketplace，可以直接复制 Skill 文件夹。

macOS / Linux：

```bash
git clone https://github.com/OWNER/REPO.git
mkdir -p ~/.codex/skills
cp -R REPO/plugins/photo-ink-postcard/skills/photo-ink-postcard ~/.codex/skills/
python3 -m pip install Pillow
```

Windows PowerShell：

```powershell
git clone https://github.com/OWNER/REPO.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force "REPO\plugins\photo-ink-postcard\skills\photo-ink-postcard" "$env:USERPROFILE\.codex\skills\"
py -m pip install Pillow
```

重启 Codex，使其重新发现 Skill。

## 基本用法

将一张风景照片附在对话中，然后明确调用：

```text
使用 $photo-ink-postcard 将这张照片制作成摄影水墨明信片。
标题使用 “Emerald Stillness”，副标题使用 “A breath of autumn rests beside the water.”
```

也可以不提供文案：

```text
请使用 photo-ink-postcard 处理我附上的照片。保持原图比例，并根据画面拟定两行克制的英文文案。
```

Skill 会依次：

1. 分析照片的比例、主体、空间层级和主色，并选择上下或左右版式。
2. 读取 `references/style-routing.md`，固定选择材质基准，并按原图结构只路由一张构图基准。
3. 读取 `references/prompt-template.md`，明确内容、材质、构图三张图的不同角色，仅生成独立的无文字水墨面板。
4. 使用通用参考控制纸张、笔触、边缘、虚实与主体落点，但不复制参考图题材。
5. 调用 `compose_postcard.py` 合成实拍、水墨与英文排版。
6. 调用 `verify_postcard.py` 验证自适应画布尺寸和实拍中心安全区。

## 参考资产路由

每次生成使用“用户照片 + 固定材质基准 + 一张构图基准”。不要同时加载四张构图图，否则模型容易折中成雷同的泛山水。

| 原图特征 | 构图资产 |
| --- | --- |
| 明确主体人物与自然共同构成叙事 | `composition-human-landscape.png` |
| 明确主体动物与环境形成动作叙事 | `composition-small-focal-point.png` |
| 水面、低地平线、湿地或海岸 | `composition-horizontal-water.png` |
| 山峰、山脊、峡谷或明显斜线 | `composition-mountain-diagonal.png` |
| 小亭、小屋、塔、舟等关键小焦点 | `composition-small-focal-point.png` |
| 林海、雾林、丘陵或多层植被 | `composition-layered-forest.png` |

`style-material-reference.png` 始终只控制纸色、矿物色、水墨渗化、干湿笔触和柔和边缘。详细优先级与冲突处理见 `references/style-routing.md`。

人物模式不会把所有游客都搬进插画。Skill 会保留最明确的叙事主体及其位置、姿态、朝向与一个主要服装色块，删除其他路人；人物通常只占插画面板的 2–7%，并压缩为约 4–7 笔抽象水墨，不生成五官、衣褶或完整写实轮廓，也不把人放大成海报主角。

动物模式比普通风景更严格地做减法：每只动物约使用 5–9 个相互呼应的墨形，只保留耳形、背弧、尾势或少量断裂条纹等必要识别点；不生成眼睛、毛发、爪或完整写实解剖。环境只保留 2–3 个大形体，避免结果变成写实水彩动物画。

## 手动合成

如果已经拥有照片和水墨插画，可以直接运行：

```bash
python plugins/photo-ink-postcard/skills/photo-ink-postcard/scripts/compose_postcard.py \
  --photo path/to/photo.jpg \
  --illustration path/to/ink-panel.png \
  --title "Emerald Stillness" \
  --subtitle "A breath of autumn rests beside the water." \
  --layout auto \
  --output output/postcard.png
```

Windows PowerShell：

```powershell
py "plugins\photo-ink-postcard\skills\photo-ink-postcard\scripts\compose_postcard.py" `
  --photo "path\to\photo.jpg" `
  --illustration "path\to\ink-panel.png" `
  --title "Emerald Stillness" `
  --subtitle "A breath of autumn rests beside the water." `
  --layout auto `
  --output "output\postcard.png"
```

验证结果：

```bash
python plugins/photo-ink-postcard/skills/photo-ink-postcard/scripts/verify_postcard.py \
  --photo path/to/photo.jpg \
  --postcard output/postcard.png
```

## 字体与样式定制

指定自定义字体：

```bash
python compose_postcard.py \
  --photo photo.jpg \
  --illustration ink.png \
  --title "Quiet Valley" \
  --subtitle "Autumn light rests beneath the snow." \
  --title-font /path/to/handwriting-font.ttf \
  --subtitle-font /path/to/sans-font.ttf \
  --output postcard.png
```

建议使用带连笔结构、但装饰不过度的手写字体。不要使用普通衬线斜体代替手写体。字体文件的授权由使用者自行确认。

## 常见问题

### 插画总是变成三条横向色带

确保图像生成时读取内容照片、`assets/style-material-reference.png` 与路由选出的一张构图基准，并明确三张图的不同角色。不要同时加载多张构图基准，也不要删除提示词中的“边角构图、轮廓局部消失、禁止贯穿全幅色带”等约束。

### 4:3 照片出现左右模糊补带

不要让生成模型制作整张明信片。只生成独立插画面板，再交给确定性脚本合成。脚本会让两个视觉区共同继承原照片比例。

### 竖向照片在竖版明信片中过窄

保留默认的 `--layout auto`。当照片宽高比小于 1 时，脚本会自动改为 4:3 横版：左侧原照、右侧同尺寸水墨面板，两行英文仍以整张画布水平居中置底。只有在明确需要固定版式时才使用 `--layout vertical` 或 `--layout horizontal` 覆盖自动路由。

### 动物插画过于写实或环境太满

确认提示词启用了“动物主体”处理：身体压缩为 5–9 个墨形，物种识别记号不超过 2–3 处，环境不超过 2–3 个大形体，纸面或极淡色域保持 62–75%。不要只降低饱和度；应实际删除毛发、条纹、岩石和背景层级。

### 标题字体不正确

运行 `check_environment.py` 查看是否发现手写字体；若没有，安装一款授权允许的手写字体，并通过 `--title-font` 指定其路径。

### 报错 `No module named PIL`

```bash
python -m pip install Pillow
```

## 发布到自己的 GitHub

在本目录中执行：

```bash
git init
git add .
git commit -m "Initial release of photo-ink-postcard"
git branch -M main
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

发布前请检查：

- 将教程中的 `OWNER/REPO` 替换为真实仓库地址。
- 根据需要修改 `plugin.json` 中的作者信息。
- 确认没有提交私人照片、真实姓名、密钥或本机绝对路径。
- 如修改功能，递增插件版本号。
- 在全新目录中重新安装并完成一次端到端测试。

## 许可证

代码、Skill 指令和随包通用参考资产采用 MIT License。使用者仍需自行确认输入照片、字体和生成结果的使用权。

## 官方资料

- [OpenAI：Skills 概念](https://developers.openai.com/plugins/concepts/skills)
- [OpenAI：打包与分发 Plugins](https://developers.openai.com/plugins/build/plugins)
- [OpenAI：Skills API 与 ZIP 上传](https://developers.openai.com/api/docs/guides/tools-skills)
