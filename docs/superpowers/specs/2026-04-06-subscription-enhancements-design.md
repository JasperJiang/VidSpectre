# VidSpectre 订阅增强功能设计

## 概述

为 VidSpectre 添加两个功能：
1. 电视剧订阅增加"快速已看"按钮
2. 订阅列表增加类型筛选器

## 功能1: 快速已看按钮

### 需求
- 给电视剧类型的订阅项添加"已看"按钮
- 点击后自动为当前已看集数加一
- 如果当前没有已看集数则默认改成 1
- 更新后同步更新数据库

### 位置
- 显示在订阅卡片中，与"爬取"按钮并排（爬取按钮左侧）

### 交互逻辑
1. 点击按钮后，获取当前 `current_episode` 值
2. 如果为 `null` 或空字符串 → 设为 `"1"`
3. 如果有值 → 提取字符串中最后一个数字序列并 +1
   - `"S01E05"` → 提取 `5` → `6`
   - `"12"` → `12 + 1` → `"13"`
4. 调用 `PUT /api/subscriptions/<sub_id>` 更新数据库
5. 成功后更新输入框显示新值

### API
- 复用现有 `PUT /api/subscriptions/<sub_id>` 接口
- 请求体: `{"current_episode": "6"}`

## 功能2: 类型筛选器

### 需求
- 订阅列表增加类型筛选功能
- 筛选项: 全部 / 电影 / 电视剧

### 位置
- "我的订阅" 标题下方，手动执行区域上方

### UI
```html
<div class="flex gap-2 mb-4">
    <button class="filter-btn active bg-blue-600" data-filter="all">全部</button>
    <button class="filter-btn bg-gray-600" data-filter="movie">电影</button>
    <button class="filter-btn bg-gray-600" data-filter="tv">电视剧</button>
</div>
```

### 交互逻辑
1. 默认选中"全部"，显示所有订阅卡片
2. 点击筛选按钮时，更新按钮激活状态
3. 前端遍历 `.subscription-card`，根据 `data-media-type` 属性显示/隐藏
4. 纯前端实现，无需刷新页面

### HTML变更
- 在 `.subscription-card` 添加 `data-media-type="{{ sub.media_type }}"` 属性

## 修改文件

1. `templates/index.html` - 添加筛选器UI、修改订阅卡片结构、添加已看按钮
2. `static/js/app.js` - 添加已看按钮逻辑、添加筛选器逻辑

## 验证方式
1. 启动开发服务器 `uv run python run.py`
2. 打开 http://localhost:5002
3. 测试快速已看按钮：点击电视剧卡片的"已看"按钮，验证集数+1
4. 测试类型筛选：点击"电影"/"电视剧"按钮，验证列表正确过滤