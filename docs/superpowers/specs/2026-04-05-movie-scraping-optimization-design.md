# 电影爬取优化设计

## 概述

优化 VidSpectre 的搜索结果展示和电影订阅的交互逻辑。

## 需求 1：搜索结果 UI 改进

### 现状
搜索结果中每个条目显示媒体名称和类型标签（电视剧/电影），无封面图。

### 改进方案
- 移除类型标签（电视剧/电影文字）
- 显示封面图片，使用 btbtla 插件已在 `MediaItem.cover_url` 中提供的 URL

### 实现位置
- `static/js/app.js` 中 `searchMedia()` 函数的 DOM 渲染逻辑
- 添加 `<img>` 标签，src 使用 `item.cover_url`
- 图片加载失败时显示占位背景

---

## 需求 2：电影展开交互逻辑

### 现状
所有订阅项（电影/电视剧）共用同一套展开逻辑：点击展开按钮 → 显示集数列表 → 用户选择集数 → 显示该集资源。

### 改进方案
电影不显示集数选择，直接展开并显示资源列表。

| 类型 | 展开行为 |
|------|---------|
| 电视剧 | 展开 → 显示集数列表 → 选择集 → 显示资源 |
| 电影 | 展开 → 直接显示资源列表 |

### 实现位置
- `static/js/app.js` 中 `toggleEpisode()` 函数
- 判断 `item.media_type === 'movie'`
- 电影类型：跳过 episode 选择，直接调用 `getDownloadLinks(item.media_id, null)`

### 数据流
```
用户点击展开
  → 判断 media_type
    → movie: getDownloadLinks(media_id, null) → 显示资源列表
    → tv: 显示集数列表 → 用户选择集 → getDownloadLinks(media_id, episode) → 显示资源
```

---

## 改动文件清单

| 文件 | 改动内容 |
|------|---------|
| `static/js/app.js` | 1. `searchMedia()` 添加封面图渲染，移除标签<br>2. `toggleEpisode()` 添加 movie 类型分支判断 |
| `plugins/sources/btbtla/parser.py` | 确认 `search()` 返回的 `MediaItem` 包含 `cover_url` |

---

## 测试要点

1. 搜索关键词，验证封面图显示正常、标签已移除
2. 电影订阅点击展开，验证直接显示资源列表（无集数选择）
3. 电视剧订阅点击展开，验证仍显示集数列表
4. 图片加载失败时显示占位背景
