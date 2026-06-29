# Enbox 📦

> 多平台信息聚合工具 — 将不同平台的内容汇聚到同一个页面。

## 功能

- **两种视图模式**：
  - 🕐 **时间线模式** — 所有内容按时间混合排列，不区分平台
  - 📂 **按平台模式** — 按平台类型分组展示，相同平台合并，支持 Tab 筛选
- **文章/视频**：以 **标题 + 摘要** 的形式展示
- **推文/短内容**：直接展示并支持 **折叠/展开**（类似 X 的长文展示）
- **作者标识**：YouTube、Podcast、X、雪球等多用户平台自动显示作者名
- 自动暗色模式，移动端适配

## 支持的平台

| 平台 | type | 说明 |
|------|------|------|
| Hacker News | `hackernews` | 热门帖子，直接 API |
| V2EX | `v2ex` | 热门/最新话题，直接 API |
| CoolShell | `coolshell` | 博客 RSS |
| YouTube | `youtube` | 支持 `handle` + `channel_id`，RSS 优先 + 页面抓取兜底 |
| Apple Podcast | `podcast` | 支持 Apple Podcast URL/ID（自动解析 RSS）或直接 RSS |
| X / Twitter | `twitter` | GraphQL API（支持 auth_token 获取最新，无认证时返回热门推文） |
| 雪球 | `xueqiu` | 通过 RSSHub 获取用户动态 |
| 通用 RSS | `rss` | 任何标准 RSS/Atom 源 |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 编辑配置（可选，默认已配置 HN + V2EX）
cp config.example.yaml config.yaml
# 按需修改 config.yaml

# 3. 启动 / 停止
./start.sh
./stop.sh
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

### YouTube

使用 `handle`（频道 @用户名）和 `channel_id`（频道 ID）配置。系统优先尝试 RSS，失败时自动抓取频道页面。

```yaml
  - name: YouTube - tiabtc
    type: youtube
    icon: "▶️"
    handle: "@tiabtc"
    channel_id: UCy2h-yNK9OF1kXDtT3AlF3Q
    limit: 10
```

### Apple Podcast

支持三种配置方式，推荐使用 Apple Podcast URL（自动通过 iTunes API 解析底层 RSS）：

```yaml
  # 方式 1：Apple Podcast URL（推荐）
  - name: 自习室 STUDY ROOM
    type: podcast
    icon: "🎙️"
    apple_podcast_url: https://podcasts.apple.com/us/podcast/id1726135306
    limit: 10

  # 方式 2：Apple Podcast ID
  - name: 自习室 STUDY ROOM
    type: podcast
    apple_podcast_id: "1726135306"

  # 方式 3：直接提供 RSS URL
  - name: 自习室 STUDY ROOM
    type: podcast
    url: https://www.ximalaya.com/album/80074602.xml
```

### X / Twitter

三级策略：
1. **认证模式**（配置 `auth_token`）— 获取用户真正的最新时间线
2. **Guest 模式**（无需认证）— 通过 GraphQL API 获取用户的精选/热门推文
3. **Syndication 备选** — 通过嵌入组件接口获取

```yaml
  # 基本配置（Guest 模式，返回精选推文）
  - name: X - elonmusk
    type: twitter
    icon: "𝕏"
    username: elonmusk
    limit: 15

  # 认证配置（返回真正最新推文）
  - name: X - elonmusk
    type: twitter
    icon: "𝕏"
    username: elonmusk
    auth_token: "your_auth_token_here"   # 从浏览器 Cookie 中获取
    limit: 15
```

> **如何获取 auth_token**：在浏览器中登录 x.com → 打开开发者工具 → Application → Cookies → 找到 `auth_token` 的值并复制。该 token 有效期较长，但可能在密码修改或登出后失效。

### 雪球

通过 [RSSHub](https://docs.rsshub.app/) 获取数据，需要配置 `rsshub_base` 和 `user_id`：

```yaml
  - name: 雪球 - 段永平
    type: xueqiu
    rsshub_base: https://rsshub.app
    user_id: "1247347556"
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENBOX_CONFIG` | `config.yaml` | 配置文件路径 |

## License

MIT
