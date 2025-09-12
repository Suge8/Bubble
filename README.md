# 🫧 Bubble

<p align="center">
  <strong><a href="#english">English</a></strong> | 
  <strong><a href="#zh-cn">简体中文</a></strong> | 
  <strong><a href="#ja">日本語</a></strong> | 
  <strong><a href="#fr">Français</a></strong> | 
  <strong><a href="#ko">한국어</a></strong>
</p>

---

<a name="english"></a>
## 🫧 Bubble - Your All-in-One AI Desktop Assistant

![Bubble Showcase](https://user-images.githubusercontent.com/12345/your-showcase-image.gif)  <!-- Please replace with your app showcase GIF -->

<p align="center">
  <a href="https://github.com/your-username/Bubble/releases"><img src="https://img.shields.io/github/v/release/your-username/Bubble?style=for-the-badge" alt="Latest Release"></a>
  <a href="#"><img src="https://img.shields.io/github/downloads/your-username/Bubble/total?style=for-the-badge" alt="Downloads"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/your-username/Bubble?style=for-the-badge" alt="License"></a>
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

1.  **Go to the [Releases Page](https://github.com/your-username/Bubble/releases)** 👈
2.  **Download the latest version for your OS** (macOS, Windows) (`.dmg` or `.exe`).
3.  **Install and enjoy!** 🎉

It's that simple!

### 🌟 Core Features

*   **🧠 All-in-One AI Hub**: Aggregate all AI services in one place, say goodbye to tab chaos.
*   **🖼️ Elegant Multi-Window Management**: Manage your AI conversation windows like a native app.
*   **🏠 Customizable Homepage**: Create your own navigation page for frequently used AI services.
*   **💡 Always-on**: Quickly access Bubble from the system tray/menu bar, always ready.
*   **🔒 Privacy First**: Bubble is just a web wrapper. Your session data communicates directly with the AI service providers. We don't touch any of your private data.
*   **🌍 Multi-Language Support**: We offer interfaces in English, Chinese, Japanese, French, Korean, and more.

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
    git clone https://github.com/your-username/Bubble.git
    cd Bubble
    ```

2.  **Create and activate a virtual environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**
    ```bash
    python Bubble.py
    ```

### 📦 How to Package

We provide convenient packaging scripts.

*   **macOS**:
    ```bash
    sh tools/build_macos.sh
    ```
*   **Windows** (make sure you have `pyinstaller` installed):
    ```bash
    pyinstaller --noconfirm --onedir --windowed --icon "src/bubble/logo/icon.ico" --name "Bubble" "Bubble.py"
    ```
The packaged application will appear in the `dist` directory.

</details>

---

### ❤️ Contributing

All forms of contributions are welcome! Whether it's submitting issues, requesting new features, or sending pull requests.

### 📜 License

This project is open-sourced under the [MIT License](./LICENSE).

---

<a name="zh-cn"></a>
## 🫧 Bubble - 你的一站式 AI 桌面助理 (简体中文)

> [!NOTE]
> 完整的中文内容和英文版本一致，请向上滚动查看详细信息。这里是快速导航锚点。

<p align="center">
  <strong><a href="#english">English</a></strong> | 
  <strong><a href="#zh-cn">简体中文</a></strong> | 
  <strong><a href="#ja">日本語</a></strong> | 
  <strong><a href="#fr">Français</a></strong> | 
  <strong><a href="#ko">한국어</a></strong>
</p>

---

<a name="ja"></a>
## 🫧 Bubble - あなたのオールインワンAIデスクトップアシスタント (日本語)

> [!NOTE]
> 完全な日本語の内容は英語版と同じです。詳細については上にスクロールしてください。これはクイックナビゲーションアンカーです。

<p align="center">
  <strong><a href="#english">English</a></strong> | 
  <strong><a href="#zh-cn">简体中文</a></strong> | 
  <strong><a href="#ja">日本語</a></strong> | 
  <strong><a href="#fr">Français</a></strong> | 
  <strong><a href="#ko">한국어</a></strong>
</p>

---

<a name="fr"></a>
## 🫧 Bubble - Votre Assistant de Bureau IA Tout-en-Un (Français)

> [!NOTE]
> Le contenu complet en français est identique à la version anglaise. Veuillez faire défiler vers le haut pour plus de détails. Ceci est une ancre de navigation rapide.

<p align="center">
  <strong><a href="#english">English</a></strong> | 
  <strong><a href="#zh-cn">简体中文</a></strong> | 
  <strong><a href="#ja">日本語</a></strong> | 
  <strong><a href="#fr">Français</a></strong> | 
  <strong><a href="#ko">한국어</a></strong>
</p>

---

<a name="ko"></a>
## 🫧 Bubble - 당신의 올인원 AI 데스크톱 어시스턴트 (한국어)

> [!NOTE]
> 전체 한국어 내용은 영어 버전과 동일합니다. 자세한 내용은 위로 스크롤하십시오. 이것은 빠른 탐색 앵커입니다.

<p align="center">
  <strong><a href="#english">English</a></strong> | 
  <strong><a href="#zh-cn">简体中文</a></strong> | 
  <strong><a href="#ja">日本語</a></strong> | 
  <strong><a href="#fr">Français</a></strong> | 
  <strong><a href="#ko">한국어</a></strong>
</p>