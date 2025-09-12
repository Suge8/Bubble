# 🫧 Bubble

<p align="center">
  <strong><a href="#zh-cn">简体中文</a></strong> |
  <strong><a href="#english">English</a></strong> |
  <strong><a href="#ja">日本語</a></strong> |
  <strong><a href="#fr">Français</a></strong> |
  <strong><a href="#ko">한국어</a></strong> |
  <strong><a href="#es">Español</a></strong> |
  <strong><a href="#de">Deutsch</a></strong> |
  <strong><a href="#ru">Русский</a></strong>
</p>

---

<a name="zh-cn"></a>
## 🫧 Bubble - 你的一站式 AI 桌面助理

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="最新发布"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="下载量"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="许可证"></a>
</p>

还在为不同 AI 服务在几十个浏览器标签页之间切换而烦恼吗？🤯 **Bubble** 将你所有喜欢的 AI 助手打包到一个流畅、精美的桌面应用中！

一次登录，随处使用。体验前所未有的效率和专注。🚀

### ✨ 支持的平台

我们集成了市面上所有主流的大语言模型，包括：

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- and more... -->
</p>

---

## 👨‍💻 用户：下载即用！

我们为你准备好了一切！无需复杂的设置。

1.  **前往 [发布页面](https://github.com/Suge8/Bubble/releases)** 👈
2.  **为你的操作系统下载最新版本** (macOS, Windows) (`.dmg` 或 `.exe`)。
3.  **安装并享受！** 🎉

就是这么简单！

### 🌟 核心功能

*   **🧠 一站式 AI 中心**: 聚合所有 AI 服务于一处，告别繁杂的标签页。
*   **🤫 防屏幕捕捉**: Bubble 不会被会议软件或录屏工具捕捉。
*   **🪟 独立会话隔离**：每个窗口可登录不同账号，信息完全独立互不干扰。
*   **🚀 后台极速并行**: 新窗口自动在后台闪电加载，随时可用而不占前台。
*   **⚡️ 快捷切换**: 使用全局快捷键 Command+G，一键显示/隐藏并切换窗口。
*   **🖼️ 优雅的多窗口管理**: 像原生应用一样流畅管理你的 AI 对话窗口。
*   **🔒 隐私优先**: Bubble 仅是网页封装器，会话数据直接与 AI 服务商通信，我们不会接触你的任何隐私信息。

---

## 🛠️ 开发者：欢迎加入！

我们热爱开源社区！如果你想为 Bubble 做出贡献或自行构建，请参考以下指南。

<details>
<summary><strong>技术栈、项目结构和构建指南</strong></summary>

### 🤖 技术栈

*   **核心框架**: Python
*   **GUI**: `pywebview` (一个轻量级的跨平台 webview 封装库)
*   **打包工具**: `pyinstaller`

### 📂 项目结构

```
/Users/sugeh/Documents/Project/Bubble/
├── Bubble.py             # 应用主入口点
├── requirements.txt      # Python 依赖
├── setup.py              # 构建配置
├── src/
│   └── bubble/
│       ├── app.py        # 核心应用逻辑和窗口管理
│       ├── main.py       # 主程序启动脚本
│       ├── components/   # UI 和功能模块 (配置、主页等)
│       ├── models/       # AI 窗口和平台配置
│       ├── assets/       # 图标、CSS、JS 等静态资源
│       └── i18n/         # 国际化语言文件
├── tools/
│   └── build_macos.sh    # macOS 构建脚本
└── ...
```

### ⚙️ 从源码运行

1.  **克隆仓库**
    ```bash
    git clone https://github.com/Suge8/Bubble.git
    cd Bubble
    ```

2. **创建虚拟环境并安装依赖**
    ```bash
    python3 -m venv .venv
    ./.venv/bin/python -m pip install --upgrade pip setuptools wheel
    ./.venv/bin/python -m pip install -r requirements.txt
    ```

3. **运行应用**
    ```bash
    ./.venv/bin/python Bubble.py
    ```

### 📦 如何打包

我们提供了便捷的打包脚本。

*   **macOS**:
    ```bash
    VIRTUAL_ENV=$PWD/.venv sh tools/build_macos.sh --install-deps
    ```

打包好的应用将出现在 `dist` 目录中。

</details>

---

### ❤️ 贡献

欢迎各种形式的贡献！无论是提交问题、请求新功能还是发送拉取请求。

### 📜 许可证

本项目基于 [MIT 许可证](./LICENSE) 开源。

---

<a name="english"></a>
## 🫧 Bubble - Your All-in-One AI Desktop Assistant

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- Please replace with your app showcase GIF -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="Latest Release"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="Downloads"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="License"></a>
</p>

Tired of juggling dozens of browser tabs for different AI services? 🤯 **Bubble** packs all your favorite AI assistants into one sleek, smooth desktop application!

Log in once, and use them everywhere. Experience unprecedented efficiency and focus. 🚀

### ✨ Supported Platforms

We integrate all major large language models on the market, including:

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- and more... -->
</p>

---

## 👨‍💻 For Users: Download and Go!

We've prepared everything for you! No complex setup required.

1.  **Go to the [Releases Page](https://github.com/Suge8/Bubble/releases)** 👈
2.  **Download the latest version for your OS** (macOS, Windows) (`.dmg` or `.exe`).
3.  **Install and enjoy!** 🎉

It's that simple!

### 🌟 Core Features

*   **🧠 All-in-One AI Hub**: Gather all AI services in one place, no more messy tabs.
*   **🤫 Screen Capture Proof**: Bubble cannot be recorded by meeting software or screen recorders.
*   **🪟 Isolated Sessions**: Each window can log into a different account, fully separated and independent.
*   **🚀 Background Fast Loading**: New windows load instantly in the background, always ready without occupying the front.
*   **⚡️ Quick Switching**: Use the global shortcut Command+G to instantly show/hide and switch windows.
*   **🖼️ Elegant Multi-Window Management**: Manage AI chat windows smoothly like a native app.
*   **🔒 Privacy First**: Bubble is just a web wrapper. Your data communicates directly with AI providers—we never touch your private info.

---

## 🛠️ For Developers: Welcome Aboard!

We love the open-source community! If you want to contribute to Bubble or build it yourself, please refer to the following guide.

<details>
<summary><strong>Tech Stack, Project Structure, and Build Guide</strong></summary>

### 🤖 Tech Stack

*   **Core Framework**: Python
*   **GUI**: `pywebview` (a lightweight cross-platform webview wrapper)
*   **Bundler**: `pyinstaller`

### 📂 Project Structure

```
/Users/sugeh/Documents/Project/Bubble/
├── Bubble.py             # Application main entry point
├── requirements.txt      # Python dependencies
├── setup.py              # Build configuration
├── src/
│   └── bubble/
│       ├── app.py        # Core app logic and window management
│       ├── main.py       # Main program startup script
│       ├── components/   # UI and feature modules (config, homepage, etc.)
│       ├── models/       # AI window and platform configuration
│       ├── assets/       # Static assets like icons, CSS, JS
│       └── i18n/         # Internationalization language files
├── tools/
│   └── build_macos.sh    # macOS build script
└── ...
```

### ⚙️ Running from Source

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Suge8/Bubble.git
    cd Bubble
    ```

2. **Create a virtual environment and install dependencies**
    ```bash
    python3 -m venv .venv
    ./.venv/bin/python -m pip install --upgrade pip setuptools wheel
    ./.venv/bin/python -m pip install -r requirements.txt
    ```

3. **Run the application**
    ```bash
    ./.venv/bin/python Bubble.py
    ```

### 📦 How to Package

We provide convenient packaging scripts.

*   **macOS**:
    ```bash
    VIRTUAL_ENV=$PWD/.venv sh tools/build_macos.sh --install-deps
    ```
    
The packaged application will appear in the `dist` directory.

</details>

---

### ❤️ Contributing

All forms of contributions are welcome! Whether it's submitting issues, requesting new features, or sending pull requests.

### 📜 License

This project is open-sourced under the [MIT License](./LICENSE).

---
<a name="ja"></a>
## 🫧 Bubble - あなたのオールインワンAIデスクトップアシスタント (日本語)

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- アプリのショーケースGIFに置き換えてください -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="最新リリース"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="ダウンロード数"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="ライセンス"></a>
</p>

さまざまなAIサービスのために何十ものブラウザタブを使い分けるのにうんざりしていませんか？🤯 **Bubble**は、お気に入りのAIアシスタントをすべて、洗練されたスムーズなデスクトップアプリケーションにまとめます！

一度ログインすれば、どこでも使えます。前例のない効率と集中力を体験してください。🚀

### ✨ 対応プラットフォーム

市場の主要な大規模言語モデルをすべて統合しています：

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- and more... -->
</p>

---

## 👨‍💻 ユーザー向け：ダウンロードしてすぐに使える！

すべて準備済みです！複雑な設定は不要です。

1.  **[リリースベージ](https://github.com/Suge8/Bubble/releases)にアクセス** 👈
2.  **お使いのOS用の最新バージョンをダウンロード** (macOS, Windows) (`.dmg` または `.exe`)。
3.  **インストールしてお楽しみください！** 🎉

とてもシンプルです！

### 🌟 主な機能

*   **🧠 オールインワンAIハブ**: すべてのAIサービスを一か所に集約、タブの煩雑さにさようなら。
*   **🤫 画面キャプチャ防止**: Bubbleは会議ソフトや録画ツールに映りません。
*   **🪟 独立セッション分離**: 各ウィンドウで異なるアカウントにログイン可能、完全に独立して干渉なし。
*   **🚀 バックグラウンド高速並行処理**: 新しいウィンドウはバックグラウンドで瞬時に読み込み、常に利用可能。
*   **⚡️ クイックスイッチ**: グローバルショートカット Command+G で即座に表示/非表示や切り替え。
*   **🖼️ 洗練されたマルチウィンドウ管理**: ネイティブアプリのようにスムーズに管理。
*   **🔒 プライバシー最優先**: Bubbleは単なるウェブラッパー。データはAIサービス提供者と直接通信し、私たちはプライバシーに一切触れません。


---

## 🛠️ 開発者向け：ようこそ！

私たちはオープンソースコミュニティが大好きです！Bubbleに貢献したい、または自分でビルドしたい場合は、以下のガイドを参照してください。

<details>
<summary><strong>技術スタック、プロジェクト構造、ビルドガイド</strong></summary>

(内容は英語セクションと同じです)

</details>

---

### ❤️ 貢献

あらゆる形の貢献を歓迎します！問題の報告、新機能の要望、プルリクエストの送信など。

### 📜 ライセンス

このプロジェクトは[MITライセンス](./LICENSE)の下でオープンソース化されています。

---

<a name="fr"></a>
## 🫧 Bubble - Votre Assistant de Bureau IA Tout-en-Un (Français)

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- Veuillez remplacer par votre GIF de présentation de l'application -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="Dernière version"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="Téléchargements"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="Licence"></a>
</p>

Fatigué de jongler avec des dizaines d'onglets de navigateur pour différents services d'IA ? 🤯 **Bubble** regroupe tous vos assistants IA préférés dans une seule application de bureau élégante et fluide !

Connectez-vous une fois et utilisez-les partout. Découvrez une efficacité et une concentration sans précédent. 🚀

### ✨ Plateformes prises en charge

Nous intégrons tous les principaux grands modèles de langage du marché, y compris :

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- et plus... -->
</p>

---

## 👨‍💻 Pour les utilisateurs : Téléchargez et c'est parti !

Nous avons tout préparé pour vous ! Aucune configuration complexe n'est requise.

1.  **Allez sur la [page des versions](https://github.com/Suge8/Bubble/releases)** 👈
2.  **Téléchargez la dernière version pour votre SE** (macOS, Windows) (`.dmg` ou `.exe`).
3.  **Installez et profitez !** 🎉

C'est aussi simple que ça !

### 🌟 Fonctionnalités principales

*   **🧠 Hub IA Tout-en-Un** : Regroupez tous vos services IA en un seul endroit, finies les dizaines d’onglets.
*   **🤫 Anti-Capture d’Écran** : Bubble n’apparaît pas dans les logiciels de réunion ni les enregistreurs d’écran.
*   **🪟 Sessions Isolées** : Chaque fenêtre peut se connecter à un compte différent, totalement indépendante.
*   **🚀 Chargement Rapide en Arrière-Plan** : Les nouvelles fenêtres se chargent instantanément en arrière-plan, prêtes à l’emploi.
*   **⚡️ Bascule Instantanée** : Utilisez le raccourci global Command+G pour afficher/masquer et changer de fenêtre en un clin d’œil.
*   **🖼️ Gestion Élégante Multi-Fenêtres** : Gérez vos fenêtres de conversation IA aussi facilement qu’une application native.
*   **🔒 Confidentialité d’Abord** : Bubble est seulement un conteneur web. Vos données communiquent directement avec les services IA, nous n’accédons jamais à vos informations privées.

---

## 🛠️ Pour les développeurs : Bienvenue à bord !

Nous aimons la communauté open-source ! Si vous souhaitez contribuer à Bubble ou le construire vous-même, veuillez consulter le guide suivant.

<details>
<summary><strong>Pile technologique, structure du projet et guide de construction</strong></summary>

(Le contenu est le même que la section anglaise)

</details>

---

### ❤️ Contribuer

Toutes les formes de contributions sont les bienvenues ! Qu'il s'agisse de soumettre des problèmes, de demander de nouvelles fonctionnalités ou d'envoyer des pull requests.

### 📜 Licence

Ce projet est open-source sous la [Licence MIT](./LICENSE).

---

<a name="ko"></a>
## 🫧 Bubble - 당신의 올인원 AI 데스크톱 어시스턴트 (한국어)

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- 앱 쇼케이스 GIF로 교체해주세요 -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="최신 릴리스"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="다운로드"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="라이선스"></a>
</p>

다양한 AI 서비스를 위해 수십 개의 브라우저 탭을 저글링하는 데 지치셨나요? 🤯 **Bubble**은 여러분이 가장 좋아하는 AI 어시스턴트를 하나의 세련되고 부드러운 데스크톱 애플리케이션에 모두 담았습니다!

한 번 로그인하면 어디서든 사용할 수 있습니다. 전례 없는 효율성과 집중력을 경험하세요. 🚀

### ✨ 지원되는 플랫폼

시장의 모든 주요 대규모 언어 모델을 통합합니다:

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- and more... -->
</p>

---

## 👨‍💻 사용자용: 다운로드하고 바로 사용하세요!

모든 것을 준비했습니다! 복잡한 설정이 필요 없습니다.

1.  **[릴리스 페이지](https://github.com/Suge8/Bubble/releases)로 이동** 👈
2.  **사용 중인 OS에 맞는 최신 버전을 다운로드하세요** (macOS, Windows) (`.dmg` 또는 `.exe`).
3.  **설치하고 즐기세요!** 🎉

정말 간단합니다!

### 🌟 핵심 기능

*   **🧠 올인원 AI 허브**: 모든 AI 서비스를 한곳에 모아 탭 혼란을 끝냅니다.
*   **🤫 화면 캡처 방지**: Bubble은 회의 소프트웨어나 녹화 도구에 잡히지 않습니다.
*   **🪟 독립 세션 분리**: 각 창마다 다른 계정으로 로그인 가능하며, 정보는 완전히 분리됩니다.
*   **🚀 백그라운드 초고속 병행 실행**: 새 창은 백그라운드에서 즉시 로드되어 언제든 바로 사용 가능합니다.
*   **⚡️ 빠른 전환**: 전역 단축키 Command+G로 창을 즉시 표시/숨기고 전환합니다.
*   **🖼️ 우아한 다중 창 관리**: 네이티브 앱처럼 매끄럽게 AI 대화 창을 관리합니다.
*   **🔒 프라이버시 우선**: Bubble은 단순한 웹 래퍼일 뿐입니다. 데이터는 AI 서비스 제공업체와 직접 통신하며, 저희는 개인 정보에 절대 접근하지 않습니다.


---

## 🛠️ 개발자용: 환영합니다!

저희는 오픈 소스 커뮤니티를 사랑합니다! Bubble에 기여하거나 직접 빌드하고 싶다면 다음 가이드를 참조하세요.

<details>
<summary><strong>기술 스택, 프로젝트 구조 및 빌드 가이드</strong></summary>

(내용은 영어 섹션과 동일합니다)

</details>

---

### ❤️ 기여

모든 형태의 기여를 환영합니다! 이슈 제출, 새로운 기능 요청, 풀 리퀘스트 전송 등 무엇이든 좋습니다.

### 📜 라이선스

이 프로젝트는 [MIT 라이선스](./LICENSE)에 따라 오픈 소스로 제공됩니다.

---

<a name="es"></a>
## 🫧 Bubble - Tu Asistente de Escritorio de IA Todo en Uno (Español)

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- Por favor, reemplaza con tu GIF de demostración de la aplicación -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="Última versión"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="Descargas"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="Licencia"></a>
</p>

¿Cansado de hacer malabares con docenas de pestañas de navegador para diferentes servicios de IA? 🤯 ¡**Bubble** empaqueta todos tus asistentes de IA favoritos en una sola aplicación de escritorio elegante y fluida!

Inicia sesión una vez y úsalos en todas partes. Experimenta una eficiencia y un enfoque sin precedentes. 🚀

### ✨ Plataformas Soportadas

Integramos todos los principales modelos de lenguaje grandes del mercado, incluyendo:

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- y más... -->
</p>

---

## 👨‍💻 Para Usuarios: ¡Descarga y Listo!

¡Hemos preparado todo para ti! No se requiere una configuración compleja.

1.  **Ve a la [Página de Versiones](https://github.com/Suge8/Bubble/releases)** 👈
2.  **Descarga la última versión para tu SO** (macOS, Windows) (`.dmg` o `.exe`).
3.  **¡Instala y disfruta!** 🎉

¡Así de simple!

### 🌟 Características Principales

*   **🧠 Centro de IA Todo-en-Uno**: Reúne todos los servicios de IA en un solo lugar, adiós a las pestañas desordenadas.
*   **🤫 A Prueba de Captura de Pantalla**: Bubble no puede ser grabado por software de reuniones ni grabadores de pantalla.
*   **🪟 Sesiones Aisladas**: Cada ventana puede iniciar sesión en una cuenta diferente, completamente separada e independiente.
*   **🚀 Carga Rápida en Segundo Plano**: Las nuevas ventanas se cargan al instante en segundo plano, siempre listas sin ocupar el frente.
*   **⚡️ Cambio Rápido**: Usa el atajo global Command+G para mostrar/ocultar y cambiar ventanas al instante.
*   **🖼️ Gestión Elegante de Múltiples Ventanas**: Administra tus chats de IA tan fluido como una app nativa.
*   **🔒 Privacidad Primero**: Bubble es solo un contenedor web. Tus datos se comunican directamente con el proveedor de IA; nunca accedemos a tu información privada.


---

## 🛠️ Para Desarrolladores: ¡Bienvenidos a Bordo!

¡Amamos a la comunidad de código abierto! Si quieres contribuir a Bubble o construirlo tú mismo, consulta la siguiente guía.

<details>
<summary><strong>Stack Tecnológico, Estructura del Proyecto y Guía de Construcción</strong></summary>

(El contenido es el mismo que la sección en inglés)

</details>

---

### ❤️ Contribuciones

¡Todas las formas de contribución son bienvenidas! Ya sea enviando issues, solicitando nuevas características o enviando pull requests.

### 📜 Licencia

Este proyecto es de código abierto bajo la [Licencia MIT](./LICENSE).

---

<a name="de"></a>
## 🫧 Bubble - Dein All-in-One KI-Desktop-Assistent (Deutsch)

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- Bitte durch dein App-Showcase-GIF ersetzen -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="Neueste Version"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="Downloads"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="Lizenz"></a>
</p>

Hast du es satt, mit Dutzenden von Browser-Tabs für verschiedene KI-Dienste zu jonglieren? 🤯 **Bubble** packt all deine bevorzugten KI-Assistenten in eine elegante, reibungslose Desktop-Anwendung!

Einmal einloggen und überall nutzen. Erlebe beispiellose Effizienz und Konzentration. 🚀

### ✨ Unterstützte Plattformen

Wir integrieren alle wichtigen großen Sprachmodelle auf dem Markt, einschließlich:

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- und mehr... -->
</p>

---

## 👨‍💻 Für Benutzer: Herunterladen und loslegen!

Wir haben alles für dich vorbereitet! Keine komplexe Einrichtung erforderlich.

1.  **Gehe zur [Releases-Seite](https://github.com/Suge8/Bubble/releases)** 👈
2.  **Lade die neueste Version für dein Betriebssystem herunter** (macOS, Windows) (`.dmg` oder `.exe`).
3.  **Installieren und genießen!** 🎉

So einfach ist das!

### 🌟 Kernfunktionen

*   **🧠 All-in-One KI-Zentrum**: Alle KI-Dienste an einem Ort, Schluss mit dem Tab-Chaos.
*   **🤫 Bildschirmaufnahme-Schutz**: Bubble kann weder von Meeting-Software noch von Aufnahme-Tools erfasst werden.
*   **🪟 Isolierte Sitzungen**: Jedes Fenster kann sich mit einem anderen Konto anmelden, vollständig getrennt und unabhängig.
*   **🚀 Schnelles Laden im Hintergrund**: Neue Fenster starten blitzschnell im Hintergrund und sind sofort einsatzbereit.
*   **⚡️ Schnelles Umschalten**: Mit dem globalen Shortcut Command+G Fenster sofort anzeigen, ausblenden oder wechseln.
*   **🖼️ Elegante Multi-Fenster-Verwaltung**: Verwalte deine KI-Chatfenster so reibungslos wie in einer nativen App.
*   **🔒 Datenschutz an erster Stelle**: Bubble ist nur ein Web-Wrapper. Deine Daten kommunizieren direkt mit den KI-Diensten; wir greifen niemals auf private Informationen zu.


---

## 🛠️ Für Entwickler: Willkommen an Bord!

Wir lieben die Open-Source-Community! Wenn du zu Bubble beitragen oder es selbst erstellen möchtest, befolge bitte die folgende Anleitung.

<details>
<summary><strong>Technologie-Stack, Projektstruktur und Bauanleitung</strong></summary>

(Der Inhalt ist derselbe wie im englischen Abschnitt)

</details>

---

### ❤️ Mitwirken

Alle Formen von Beiträgen sind willkommen! Ob es sich um das Einreichen von Problemen, das Anfordern neuer Funktionen oder das Senden von Pull-Requests handelt.

### 📜 Lizenz

Dieses Projekt ist unter der [MIT-Lizenz](./LICENSE) quelloffen.

---

<a name="ru"></a>
## 🫧 Bubble - Ваш универсальный ИИ-помощник для рабочего стола (Русский)

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- Пожалуйста, замените на ваш GIF-файл с демонстрацией приложения -->

<p align="center">
  <a href="https://github.com/Suge8/Bubble/releases"><img src="https://img.shields.io/github/v/release/Suge8/Bubble?style=for-the-badge" alt="Последний релиз"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/Suge8/Bubble/total?style=for-the-badge" alt="Загрузки"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/Suge8/Bubble?style=for-the-badge" alt="Лицензия"></a>
</p>

Устали от жонглирования десятками вкладок браузера для разных ИИ-сервисов? 🤯 **Bubble** упаковывает всех ваших любимых ИИ-помощников в одно изящное и плавное настольное приложение!

Войдите один раз и используйте их везде. Испытайте беспрецедентную эффективность и сосредоточенность. 🚀

### ✨ Поддерживаемые платформы

Мы интегрируем все основные большие языковые модели на рынке, включая:

<p align="center">
  <img src="src/bubble/assets/icons/gemini.png" width="40" alt="Gemini"> &nbsp;
  <img src="src/bubble/assets/icons/openai.png" width="40" alt="OpenAI"> &nbsp;
  <img src="src/bubble/assets/icons/claude.png" width="40" alt="Claude"> &nbsp;
  <img src="src/bubble/assets/icons/mistral.png" width="40" alt="Mistral"> &nbsp;
  <img src="src/bubble/assets/icons/grok.png" width="40" alt="Grok"> &nbsp;
  <img src="src/bubble/assets/icons/kimi.png" width="40" alt="Kimi"> &nbsp;
  <img src="src/bubble/assets/icons/qwen.png" width="40" alt="Qwen"> &nbsp;
  <img src="src/bubble/assets/icons/deepseek.png" width="40" alt="DeepSeek"> &nbsp;
  <img src="src/bubble/assets/icons/perplexity.png" width="40" alt="Perplexity"> &nbsp;
  <img src="src/bubble/assets/icons/zai.png" width="40" alt="Zai"> &nbsp;
  <!-- и другие... -->
</p>

---

## 👨‍💻 Для пользователей: Скачай и работай!

Мы все для вас подготовили! Никакой сложной настройки не требуется.

1.  **Перейдите на [страницу релизов](https://github.com/Suge8/Bubble/releases)** 👈
2.  **Загрузите последнюю версию для вашей ОС** (macOS, Windows) (`.dmg` или `.exe`).
3.  **Установите и наслаждайтесь!** 🎉

Это так просто!

### 🌟 Основные функции

*   **🧠 Универсальный центр ИИ**: Все сервисы ИИ в одном месте — забудьте о хаосе вкладок.
*   **🤫 Защита от записи экрана**: Bubble не отображается в программах для конференций или записи экрана.
*   **🪟 Изолированные сессии**: В каждом окне можно войти в разные аккаунты, полностью независимо друг от друга.
*   **🚀 Быстрая работа в фоне**: Новые окна мгновенно загружаются в фоновом режиме, всегда готовы к использованию.
*   **⚡️ Быстрое переключение**: Используйте глобальное сочетание Command+G для мгновенного показа/скрытия и переключения окон.
*   **🖼️ Удобное управление несколькими окнами**: Управляйте чатами с ИИ так же легко, как в нативном приложении.
*   **🔒 Конфиденциальность превыше всего**: Bubble — это всего лишь веб-обёртка. Ваши данные напрямую передаются провайдерам ИИ, мы не имеем к ним доступа.


---

## 🛠️ Для разработчиков: Добро пожаловать!

Мы любим сообщество с открытым исходным кодом! Если вы хотите внести свой вклад в Bubble или собрать его самостоятельно, пожалуйста, обратитесь к следующему руководству.

<details>
<summary><strong>Технологический стек, структура проекта и руководство по сборке</strong></summary>

(Содержание такое же, как в английской секции)

</details>

---

### ❤️ Вклад

Приветствуются любые формы вклада! Будь то отправка отчетов о проблемах, запрос новых функций или отправка pull-запросов.

### 📜 Лицензия

Этот проект с открытым исходным кодом распространяется под [лицензией MIT](./LICENSE).
