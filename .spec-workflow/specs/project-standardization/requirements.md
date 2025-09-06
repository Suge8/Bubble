# 项目规范化需求文档

## 介绍

本文档基于当前代码库的最新实现进展，更新并细化 Bubble-Bot（macOS AI 助手）项目的需求范围，覆盖首页/导航、多窗口平台管理、权限与热键、状态栏菜单、配置持久化、健康检查与稳定性、UI 与图标、打包与分发、以及测试与文档标准等方面。

## 与产品愿景的一致性

继续围绕“轻量、友好、可扩展”的 AI 伴随式体验：启动快、切换稳、配置清晰、权限可控，支持多 AI 并行，默认尊重本地数据与用户选择。

## 需求

### 需求1：主页功能与导航系统

用户故事：作为用户，我希望进入应用时首先看到友好的主页，能够选择最常使用的 AI，并在聊天页通过返回按钮回到主页管理 AI 平台。

验收标准：
1. WHEN 首次启动 THEN 显示主页并提示选择默认 AI。
2. WHEN 选择 AI THEN 跳转对应聊天页面。
3. WHEN 位于聊天页 THEN 左上角显示“返回”按钮。
4. WHEN 点击“返回” THEN 回到主页进行平台管理或重新选择。

### 需求2：多窗口 AI 平台管理系统

用户故事：作为用户，我希望能在主页增删 AI 平台，并可为同一平台创建多个窗口（多账号），顶部下拉最多显示 5 个窗口并保持并行运行。

验收标准：
1. WHEN 在主页 THEN 可增删平台；支持 openai、gemini、grok、claude、deepseek、zai、qwen。
2. WHEN 添加平台 THEN 顶部选择器可见且平台保持并行运行。
3. WHEN 需要多账号 THEN 同平台最多可开启 5 个窗口并互不干扰。
4. WHEN 管理窗口数量 THEN 下拉框最多展示 5 个窗口。
5. WHEN 删除平台 THEN 从可选项移除并同步清理相关窗口记录。
6. WHEN 完成管理 THEN 持久化用户配置。

### 需求3：聊天页面 UI 优化

用户故事：作为用户，我希望聊天页面顶部的 AI 选择下拉居中显示，切换丝滑，整体观感现代友好。

验收标准：
1. WHEN 展示聊天页 THEN 顶部 AI 选择器居中。
2. WHEN 点击选择器 THEN 展示全部已添加窗口（最多 5 个）。
3. WHEN 切换窗口 THEN 无闪烁、无显著延迟（目标 < 200ms）。
4. WHEN 优化 UI THEN 具备基础过渡与动效（淡入/淡出、尺寸/位置平滑）。

### 需求4：多 AI 并行与窗口管理

用户故事：作为用户，我希望可同时使用多个 AI 对话，每个窗口维护独立会话与登录状态；同平台多账号并行。

验收标准：
1. WHEN 切换 AI 窗口 THEN 最多 5 个窗口并行运行且状态独立。
2. WHEN 资源紧张 THEN 采用智能管理避免明显卡顿或崩溃。
3. WHEN 同平台多窗口 THEN 各自账号互不影响。

### 需求5：项目结构重构为 src 布局

用户故事：作为架构师，我希望项目采用现代化 src 布局，提升可测试性、打包可靠性与模块隔离。

验收标准：
1. WHEN 重构 THEN 源码位于 `src/bubblebot/`；测试位于 `tests/`。
2. WHEN 配置打包 THEN `pyproject.toml`/`setup.py` 支持 src 布局与入口。
3. WHEN 导入模块 THEN 全部指向 `bubblebot` 包路径正确可用。

### 需求6：代码规范化标准

用户故事：作为开发者，我希望统一代码规范，保证一致性与可维护性。

验收标准：
1. WHEN 编码 THEN 遵循 PEP 8；使用 Black（行宽 88）。
2. WHEN 定义函数/类 THEN 提供 docstring。
3. WHEN import THEN 遵循“标准库/第三方/本地”顺序。
4. WHEN 命名 THEN 遵循 snake_case/CamelCase/UPPER_SNAKE 约定。

### 需求7：文档标准化

用户故事：作为维护者，我希望提供完整的中英文文档，便于新同学快速上手。

验收标准：
1. WHEN 更新 README THEN 先中文后英文，信息等价。
2. WHEN 写 API 文档 THEN 需含功能说明、参数/返回、示例。
3. WHEN 写关键接口注释 THEN 中文为主，英文补充关键点。
4. WHEN 写架构文档 THEN 包含 Mermaid 结构图与模块说明。

### 需求8：全局热键与自定义（新增）

用户故事：作为用户，我希望通过全局快捷键快速显示/隐藏窗口，并可在应用内便捷修改该快捷键。

验收标准：
1. WHEN 初始安装 THEN 默认热键为 Command+G（可配置）。
2. WHEN 通过“Set New Trigger”菜单设置快捷键 THEN 新组合键持久化到 `~/Library/Logs/bubblebot/custom_trigger.json`，重启后仍生效。
3. WHEN 按下自定义热键 THEN 去抖与“闩锁”逻辑避免抖动和多次触发。
4. WHEN 删除 `custom_trigger.json` THEN 回退到默认热键并记录提示。

### 需求9：权限与安全（新增）

用户故事：作为用户，我希望应用在需要时请求并检测“辅助功能”和“麦克风”权限，也能在命令行主动检测权限状态。

验收标准：
1. WHEN 运行 `python -m bubblebot.main --check-permissions` THEN 返回码 0 表示已授权，否则返回 `PERMISSION_CHECK_EXIT`（值=1）。
2. WHEN 应用启动且缺少辅助功能权限 THEN 调起系统授权弹窗（可通过环境变量 `BB_NO_TAP=1` 在开发时跳过）。
3. WHEN 首次需要麦克风 THEN 请求音频权限（可通过环境变量 `BB_NO_MIC_PROMPT=1` 在开发时跳过）。
4. WHEN 权限授予 THEN 正常建立事件监听器并响应热键。

### 需求10：状态栏菜单与应用图标（新增）

用户故事：作为用户，我希望通过 macOS 状态栏图标快速访问常用操作，应用在 Dock 和状态栏展示品牌图标并自适应浅/深色模式。

验收标准：
1. WHEN 启动 THEN 在状态栏显示 BubbleBot 图标，菜单包含：Show/Hide、Home、Clear Web Cache、Set New Trigger、Install/Uninstall Autolauncher、Quit。
2. WHEN 切换浅/深色外观 THEN 状态栏图标自动切换黑/白版本（`src/bubblebot/logo/`）。
3. WHEN 打包 THEN Dock 图标使用 `logo/icon.icns`。

### 需求11：配置持久化与一致性（新增）

用户故事：作为用户和维护者，我希望平台与窗口配置可靠持久化，路径清晰统一，具备备份与迁移策略。

验收标准：
1. WHEN 主页/平台管理保存配置 THEN 写入 `~/Library/Application Support/BubbleBot/config.json`。
2. WHEN 平台管理器保存平台清单 THEN 默认写入 `~/.bubblebot/platforms.json` 并自动备份到 `~/.bubblebot/platforms_backup.json` 与时间戳备份，最多保留 5 份。
3. WHEN 后续统一配置策略 THEN 需提供迁移脚本与兼容读写（见设计文档）。

### 需求12：稳定性与健康检查（新增）

用户故事：作为用户，我希望应用在异常时能记录错误并避免频繁崩溃重启，便于定位问题。

验收标准：
1. WHEN 启动异常 THEN 记录日志到 `~/Library/Logs/bubblebot/bubblebot_error_log.txt`。
2. WHEN 在 60 秒内崩溃次数 > 3 THEN 中止继续重启并打印指引（删除计数文件以恢复）。

### 需求13：窗口顶部栏与透明度控制（新增）

用户故事：作为用户，我希望每个窗口具备最小化/关闭/透明度调节等基础控制，并保留拖拽区域。

验收标准：
1. WHEN 创建窗口 THEN 顶部栏包含关闭与最小化按钮、平台标签、透明度 +/- 控件。
2. WHEN 拖拽顶部栏 THEN 窗口跟随移动。

## 非功能性需求

### 架构与模块化
- 单一职责、模块化、依赖最小化、清晰接口；组件/工具拆分，逻辑可复用。

### 性能
- 启动 < 3s；窗口切换 < 1s；UI 交互 < 200ms；5 窗口并行稳定运行。

### 安全
- 本地处理用户数据；跨进程/框架交互采用安全方式；配置支持环境变量覆盖；权限按需提示。

### 可靠性
- 多 macOS 版本稳定运行；平台连接失败优雅降级；异常不崩溃；单窗口异常不影响其他窗口；崩溃保护与日志可用。

### 可用性
- 新用户 5 分钟内完成首启；界面直观；热键可自定义；窗口管理清晰；状态栏易用。

---

# Project Standardization Requirements (English Summary)

[Omitted for brevity in this iteration; Chinese section is canonical. English mirror to be generated during documentation polishing phase to keep both in sync.]