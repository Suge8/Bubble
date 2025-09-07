# 🫧 Bubble — 你的 macOS 轻量 AI 助手

一键呼出、悬浮置顶、即开即用。支持 ChatGPT / Claude / Grok / Gemini / Perplexity 等多模型，隐私本地首选，无需云端托管。

> 没有跟踪、没有服务端，只有高效的 AI 工作流。

---

## 🚀 快速开始

```bash
git clone git@github.com:Suge8/Bubble.git
cd Bubble

python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 开发运行（两种方式任意一种）
python Bubble.py
# 或
python -m bubble.main
```

- 已安装后（可执行脚本）：命令行运行 `bubble`

---

## ✨ 主要特性

- 悬浮小窗：始终置顶，随时写/看/问
- 多模型选择：一键切换常见 LLM 提供商
- 多窗口并行：最多 5 个窗口同时对话
- 语音输入：支持麦克风语音指令
- 全局热键：默认 ⌘ + G，可自定义
- 会议免打扰：检测会议类 App 自动隐藏
- 本地优先：配置存本地，不上传任何内容

---

## 🧱 架构概览

- HomepageManager：首启引导、平台启用与默认 AI，渲染 WebView 首页，引导配置
- NavigationController：页面状态机（homepage ↔ chat），处理返回、标题与选择器联动
- MultiWindowManager：管理最多 5 个并发窗口，几何与激活控制，按平台分组

用户配置默认保存在 `~/Library/Application Support/Bubble/config.json`（本地持久化）。

---

## 🧪 开发命令

- 本地运行：`python Bubble.py` 或 `python -m bubble.main`
- 权限检查：`python -m bubble.main --check-permissions`
- 测试：`pytest -v --tb=short`
- 格式化：`black src tests`
- Lint：`flake8 src tests && pylint src/bubble`

---

## 📦 打包应用（macOS）

```bash
python setup.py py2app
open dist/Bubble.app
```

打包产物位于：`dist/Bubble.app`

---

## 🔐 权限说明

- 🎙️ 麦克风权限：用于语音输入
- ⌨️ 辅助功能：用于全局热键

可在「系统设置 → 隐私与安全性」中管理。也可先用 `python -m bubble.main --check-permissions` 进行快速检查。

---

## 目录结构

- `src/bubble/`：核心 App（GUI、热键、管理器）
  - `app.py` / `main.py` / `listener.py`：应用入口与事件
  - `components/`：`homepage_manager.py`、`navigation_controller.py`、`multiwindow_manager.py` 等
  - `models/`：`platform_config.py` 等
  - `i18n/`：多语言资源
  - `logo/`：图标资源
- `tests/`：Pytest 测试用例
- 入口：`Bubble.py`（开发）/ `bubble`（安装后命令）

---

## 许可证

本项目采用 MIT License。

---

如果喜欢，欢迎点一个 Star 🌟
