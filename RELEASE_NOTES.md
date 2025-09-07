Bubble 0.3.0 — 多语言 README 与构建改进（2025-09-07）

亮点概览
- README 全面改版：中文优先，顶部语言切换（中/英/日/韩/法），新增 Releases 直达下载入口。
- 支持模型清单清晰：OpenAI、Claude、Grok、Gemini、Perplexity、Qwen、DeepSeek、Mistral、Kimi、ZAI。

改进与修复
- 架构说明更清晰：HomepageManager / NavigationController / MultiWindowManager 概览与本地配置路径说明。
- 构建稳定性：修复 py2app 图标路径缺失导致的失败（iconfile 存在性检测）。
- 打包资源：修正 MANIFEST.in 路径，减少打包警告；新增打包脚本根据版本输出 Bubble-v<version>.zip + SHA256。
 - 设置与性能：新增“切换页面”快捷键与“休眠时间（默认 30 分钟）”，清除缓存移动到同一行右侧；加入后台挂起策略（长时间不活动可释放资源，激活时快速恢复）；站点导航白名单与加载失败“重试”覆盖层；文档命令统一为 `python3`。

升级指引
- 前往 Releases 下载最新压缩包，解压后将 Bubble.app 拖入「应用程序」。
- 首次启动按引导授予麦克风与辅助功能权限；可用 `python -m bubble.main --check-permissions` 预检查。

Bubble 0.3.1 — 打包版启动错误修复（2025-09-08）

修复
- 解决打包版 (.app) 启动时的 PyObjC 桥接错误（BadPrototypeError/TypeError），原因是运行时签名未在打包环境正确解析。现已通过 ObjC 友好 setter 与签名修正规避，纯 Python 与打包版均可正常初始化。
- 确保 Dock/状态栏图标从 App Bundle 的 Resources 中加载（logo/icon.icns、logo/logo_white.png、logo/logo_black.png）。

说明
- 推荐下载 v0.3.1 安装包；若从源码构建，建议先清理 build/ 与 dist/ 再构建：`rm -rf build dist && python3 setup.py py2app -O2`。

Bubble 0.3.2 — Ctrl+C 行为优化与 README 同步（2025-09-08）

改进
- 仅在“源码开发的交互式终端”里响应 Ctrl+C；打包的 .app 中忽略 Ctrl+C，避免从终端调试时误触退出。
- README 同步当前功能与行为（模型列表、快速开始、SIGINT 行为说明）。

打包
- 继续输出 universal2（arm64 + x86_64）版本；包含自定义图标与状态栏图标资源。

Bubble 0.3.3 — 稳定构建与自动发布工作流（2025-09-08）

改进
- 构建更稳：`setup.py` 使用绝对 APP 路径并仅打包 `bubble` 包，避免 CI 环境路径或历史目录影响。
- 依赖补齐：增加 `packaging>=24.2`，清除 py2app 关于 packaging 的提示。
- 自动发布：新增 GitHub Actions 工作流（macOS），推送 tag 即自动构建 .app、打 zip + sha256 并附到 Release。

验证
- 本地：`rm -rf build dist && python3 -m pip install -r requirements.txt && python3 setup.py py2app -q`，运行 `BB_DEBUG=1 "dist/Bubble.app/Contents/MacOS/Bubble"`。
- CI：推送 tag（如 `v0.3.3`）会自动出包并创建 Release。

Bubble 0.3.4 — CI 构建稳定性修复（2025-09-08）

修复
- CI 环境缺少 `Bubble.py` 导致 py2app 入口丢失：在构建时自动生成 `build/py2app_launcher.py` 兜底入口，始终从 `bubble.main:main` 启动。
- 明确打包包列表：仅包含 `bubble` 相关包，避免历史 `bubblebot` 被误收集导致构建日志出现旧路径。

提示
- 给 tag（如 `v0.3.4`）即可自动触发 macOS 构建与发布（见 `.github/workflows/release-macos.yml`）。

—

Bubble 0.2.2 — 后台页面并行与无缝切换（重磅更新）

亮点概览
- 单窗口多页面：后台窗口分离，页面并行加载，切换瞬时无重载。
- 主页丝滑无骨架：后台预加载不触发骨架与闪烁；骨架仅在前台页首次加载时短暂出现。
- 下拉与页面实时同步：切页/增删页即时更新，并精确保持选中一致。
- 启动自动恢复历史页面：一进入应用即在后台预热所有曾经打开的页面；主页气泡与下拉严格对应。
- UI 稳定：平台页隐藏左上角品牌区（Logo/文字/提示气泡），主页显示；返回键负责返回主页。

详细更新
- 新增：单窗口多页面架构（后台 WKWebView 并行常驻），切换仅显隐不重载。
- 新增：应用启动后自动从配置恢复所有历史页面，并在后台加载完成，避免首次切换卡顿。
- 优化：仅当“当前前台页”处于加载中才显示骨架；主页及后台加载一律不显示骨架。
- 优化：主页点击高亮即创建该平台的第 1 个后台页；“+”继续新增，气泡与下拉即时增加。
- 优化：取消选中会批量关闭该平台所有后台页并一次性刷新 UI/下拉，避免闪烁和残留项。
- 优化：导航统一走 NavigationController，返回键、品牌显隐、下拉状态一次性同步，杜绝不同步。

升级指引
- 直接下载本 Release 附件的 ZIP，解压后将 Bubble.app 拖入“应用程序”即可。
- 若遇到首次启动被阻止，请在“系统设置 → 隐私与安全性”中允许来自已识别开发者的 App。

已知提示
- 当后台页面较多时内存占用可能增加；首次跨过 5 个页面时会有轻量 Toast 提示。

感谢使用 Bubble！欢迎反馈问题与建议，以便我们进一步优化体验。
