# Enbox 📦

> 多平台信息聚合工具 — 将不同平台的内容汇聚到同一个页面。

## 功能

- **文章/视频**：以 **标题 + 摘要** 的形式展示
- **推文/短内容**：直接展示并支持 **折叠/展开**（类似 X 的长文展示）
- 支持按信息源切换 Tab 筛选
- 自动暗色模式，移动端适配

## 支持的平台

| 平台 | type | 说明 |
|------|------|------|
| Hacker News | `hackernews` | 热门帖子，直接 API |
| V2EX | `v2ex` | 热门/最新话题，直接 API |
| CoolShell | `coolshell` | 博客 RSS |
| YouTube | `youtube` | 频道 RSS，需要 channel_id |
| Apple Podcast | `podcast` | 播客 RSS Feed |
| X / Twitter | `twitter` | 通过 RSSHub 获取用户时间线 |
| 雪球 | `xueqiu` | 通过 RSSHub 获取用户动态 |
| 通用 RSS | `rss` | 任何标准 RSS/Atom 源 |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 编辑配置（可选，默认已配置 HN + V2EX）
cp config.example.yaml config.yaml
# 按需修改 config.yaml

# 3. 启动
python main.py
```

打开浏览器访问 http://localhost:8000

## 配置说明

编辑 `config.yaml`，每个 source 包含以下字段：

```yaml
sources:
  - name: 显示名称
    type: hackernews | v2ex | rss | youtube | podcast | twitter | xueqiu | coolshell
    icon: "emoji"         # 可选，Tab 和标题前的图标
    url: "RSS Feed URL"   # RSS 类型必填
    limit: 20             # 可选，获取条数
    display: article      # 可选，article（标题+摘要）| post（折叠展开）
```

### Twitter / 雪球

这两个平台通过 [RSSHub](https://docs.rsshub.app/) 获取数据，需要：

1. 配置 `rsshub_base`（默认 `https://rsshub.app`，建议自建）
2. 配置对应的 `username`（Twitter）或 `user_id`（雪球）

```yaml
  - name: X - elonmusk
    type: twitter
    rsshub_base: https://rsshub.app
    username: elonmusk

  - name: 雪球 - 段永平
    type: xueqiu
    rsshub_base: https://rsshub.app
    user_id: "1247347556"
```

### YouTube

在频道页面 URL 中获取 channel_id：

```yaml
  - name: YouTube - Fireship
    type: youtube
    url: https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENBOX_CONFIG` | `config.yaml` | 配置文件路径 |

## License

MIT
