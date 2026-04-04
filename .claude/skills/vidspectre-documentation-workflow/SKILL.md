---
name: vidspectre-documentation-workflow
description: Use when modifying VidSpectre code - ensures project documentation stays in sync with implementation changes
---

# VidSpectre 文档更新工作流

## 概述

在 VidSpectre 项目中进行任何代码修改后，需要同步更新 `docs/PROJECT_SUMMARY.md` 和 `CLAUDE.md`，确保文档与实现保持一致。

## 何时使用

**每次代码修改后都要检查：**
- Bug 修复（特别是 `plugins/sources/` 下的插件）
- 新增 API 端点
- 数据库模型变更
- 新功能或用户可见的功能变化
- 影响现有功能行为的修改

## 必须更新的文件

### 1. docs/PROJECT_SUMMARY.md

这是项目的**变更日志**。需要记录：
- 什么发生了变化
- 为什么发生变化（bug 修复、新功能、重构）

新增内容使用 "9. ..." 这样的编号。如果 section 9 已存在，添加 section 10。

### 2. CLAUDE.md

这是项目的**参考指南**。在以下情况更新：
- 项目结构新增目录或文件
- 新增命令或脚本
- 架构决策变更
- API 端点变化
- 新增配置选项

### 3. README.md

用户面向的说明文档。新增功能、部署方式、命令时需要更新。

## 快速对照表

| 变更类型 | PROJECT_SUMMARY.md | CLAUDE.md | README.md |
|----------|--------------------|-----------|-----------|
| Bug 修复 | 添加到"Bug修复"相关章节 | 通常不需要修改 | 通常不需要修改 |
| 新功能 | 添加新的编号章节 | 如有结构/命令变化则更新 | 新增功能说明 |
| 配置变更 | 涉及用户层面则记录 | 更新配置相关章节 | 更新相关说明 |
| 新增 API | 在现有章节中补充 | 更新 API 结构说明 | 更新 API 表格 |
| Docker/部署 | 添加新的编号章节 | 更新 Commands 章节 | 添加部署说明 |

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 只更新代码，不更新文档 | 未来 Claude 无法了解项目变化 |
| 只更新一个文档 | 文档不一致会导致困惑 |
| 写成叙事故事 | 使用要点列表，保持可扫描 |

## 示例

btbtla 搜索功能的 Bug 修复：
1. 修改 `plugins/sources/btbtla/parser.py` 中的代码
2. 提交代码
3. 在 PROJECT_SUMMARY.md 添加 section 9："搜索功能Bug修复 - btbtla 搜索 URL 格式和CSS选择器修复"
4. 如果 CLAUDE.md 相关章节受影响，同步更新
