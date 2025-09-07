# 🫧 Bubble — 你的 macOS 轻量 AI 助手

[简体中文](#zh) | [English](#en) | [日本語](#ja) | [한국어](#ko) | [Français](#fr)

---

<a id="zh"></a>

## 🇨🇳 简体中文

一键呼出、悬浮置顶、即开即用。支持多家模型提供商（OpenAI、Claude、Grok、Gemini、Perplexity、Qwen、DeepSeek、Mistral、Kimi、ZAI…），隐私本地优先，无需服务端。

👉 立即下载：前往 Releases 获取最新安装包：https://github.com/Suge8/Bubble/releases/latest

推荐你在用的第一款“轻量 AI 悬浮窗”。告别切应用复制粘贴，写作 / 阅读 / 代码 / 会议边问边用，效率直线上升。

### 主要特性

- 悬浮小窗：始终置顶，随时写/看/问
- 多模型切换：常见 LLM 一键切换（OpenAI/Claude/Grok/Gemini/Perplexity/Qwen/DeepSeek/Mistral/Kimi/ZAI）
- 多窗口并行：最多 5 个窗口同时对话 / 互不打扰
- 语音输入：支持麦克风快速语音问答
- 全局热键：默认 ⌘ + G，可自定义
- 会议免打扰：检测会议类 App 自动隐藏
- 本地优先：配置仅存本机，不上传任何内容

### 系统权限

- 🎙️ 麦克风：用于语音输入
- ⌨️ 辅助功能：用于全局热键

可在「系统设置 → 隐私与安全性」管理；也可用 `python -m bubble.main --check-permissions` 预检查。

### 快速开始（面向用户）

1. 前往 Releases 下载最新 `Bubble.app` 压缩包并解压
2. 将 `Bubble.app` 拖入「应用程序」
3. 首次启动按引导授予权限，设置你常用的模型与热键

喜欢就点个 Star 支持我们，让更多人发现它！

---

### 面向开发者（简短）

开发运行：

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python Bubble.py
```

打包构建（macOS）：

```bash
python setup.py py2app
open dist/Bubble.app
```

---

### 目录与架构（概览）

- `src/bubble/` 核心 App：
  - 组件：HomepageManager（首启/平台/默认 AI）、NavigationController（主页 ↔ 聊天）、MultiWindowManager（最多 5 窗口）
  - 入口/事件：`app.py`、`main.py`、`listener.py`
  - 其它：`models/`、`i18n/`、`logo/`
- 用户配置：`~/Library/Application Support/Bubble/config.json`

---

<a id="en"></a>

## 🇺🇸 English

Bubble is a lightweight macOS AI assistant: summon with a hotkey, always-on-top mini window, multi-model switch, up to 5 concurrent chats, and privacy-first local config.

Download latest: https://github.com/Suge8/Bubble/releases/latest

Key features: floating window, global hotkey (⌘+G), voice input, meeting-aware auto-hide, local-only config. Providers: OpenAI, Claude, Grok, Gemini, Perplexity, Qwen, DeepSeek, Mistral, Kimi, ZAI.

Developers (short): create venv, `pip install -e ".[dev]"`, run with `python Bubble.py`; build with `python setup.py py2app` and open `dist/Bubble.app`.

---

<a id="ja"></a>

## 🇯🇵 日本語

Bubble は軽量な macOS 用 AI アシスタントです。ホットキーで即起動、常に最前面の小さなウィンドウ、複数モデル切替、最大 5 つの同時チャット、ローカル優先でプライバシー配慮。

最新版ダウンロード: https://github.com/Suge8/Bubble/releases/latest

開発: 仮想環境を作成し `pip install -e ".[dev]"`、`python Bubble.py` で起動。ビルドは `python setup.py py2app`、`dist/Bubble.app` を開く。

---

<a id="ko"></a>

## 🇰🇷 한국어

Bubble은 가벼운 macOS AI 도우미입니다. 단축키로 즉시 호출, 항상 위에 떠있는 미니 창, 모델 간 빠른 전환, 최대 5개 동시 대화, 로컬 우선 개인정보 보호.

최신 버전 다운로드: https://github.com/Suge8/Bubble/releases/latest

개발: 가상환경 생성 후 `pip install -e ".[dev]"`, `python Bubble.py` 실행. 빌드는 `python setup.py py2app`, `dist/Bubble.app` 실행.

---

<a id="fr"></a>

## 🇫🇷 Français

Bubble est un assistant IA léger pour macOS. Fenêtre flottante en surimpression, raccourci global (⌘+G), entrée vocale, jusqu’à 5 chats simultanés, données locales en priorité.

Télécharger la dernière version : https://github.com/Suge8/Bubble/releases/latest

Développement (court) : créer un venv, `pip install -e ".[dev]"`, lancer `python Bubble.py`. Construire avec `python setup.py py2app`, puis ouvrir `dist/Bubble.app`.

---

许可证：MIT License
