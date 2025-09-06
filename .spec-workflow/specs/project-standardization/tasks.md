- [x] 0.1 全局更名为“Bubble”（显示名与文档）
  - Files: src/bubblebot/app.py（窗口/菜单标题）、状态栏第一项提示、各组件标题；README.md/CHANGELOG.md、截图与说明；setup.py/pyproject.toml（如含 CFBundleName/DisplayName）。
  - 不改动 Python 包名与命令（bubblebot）以降低风险；如需后续再议。
  - Purpose: 统一品牌展示。

- [x] 0.2 配置路径迁移（BubbleBot → Bubble）
  - File: src/bubblebot/components/config_manager.py
  - 迁移并兼容读取：`~/Library/Application Support/BubbleBot/` → `~/Library/Application Support/Bubble/`，`~/.bubblebot/` → `~/.bubble/`；时间戳备份≤5；一次性提示。
  - Purpose: 命名一致且保护用户数据。

- [x] 1.1 建立多语言基础设施（zh/en/ja/ko/fr）
  - Files: src/bubblebot/i18n/__init__.py (new), src/bubblebot/i18n/strings_zh.json (new), src/bubblebot/i18n/strings_en.json (new), src/bubblebot/i18n/strings_ja.json (new), src/bubblebot/i18n/strings_ko.json (new), src/bubblebot/i18n/strings_fr.json (new)
  - 提供 `t(key: str, **kwargs)`；缺失键回退英文并记录告警。
  - Purpose: 统一本地化入口。

- [x] 1.2 首次运行按系统语言设置默认语言
  - Files: src/bubblebot/app.py, src/bubblebot/components/config_manager.py
  - 未设置 `language` 时读取系统 locale → 映射 zh/en/ja/ko/fr；写入并生效。
  - Purpose: 首次进入默认选择系统语言。

- [x] 1.3 运行时语言切换广播与刷新
  - Files: src/bubblebot/app.py, src/bubblebot/components/homepage_manager.py, src/bubblebot/components/navigation_controller.py
  - 语言变更后通知各视图/菜单刷新；WebView 重新渲染或注入更新。
  - Purpose: 切换后即时生效。

- [x] 1.4 本地化现有 UI 文案
  - Files: src/bubblebot/app.py, src/bubblebot/components/homepage_manager.py, src/bubblebot/components/navigation_controller.py, src/bubblebot/listener.py
  - 将可见字符串替换为 `t()`；补全多语言 JSON。
  - Purpose: 覆盖核心界面与菜单。

- [x] 1.5 窗口驻留与内存提示气泡
  - Files: src/bubblebot/components/multiwindow_manager.py, src/bubblebot/app.py
  - 新建页面默认常驻，保证多窗口可同时对话；当窗口数>5 时，在右上角显示小气泡提示“窗口过多可能占用内存”，支持关闭/不再提示；≤5 正常。
  - Purpose: 多窗口并行与友好提示。

- [x] 2.1 新建设置窗口（语言 + 开机启动 + 快捷键 + 清除缓存）
  - Files: src/bubblebot/components/settings_window.py (new)
  - NSWindow：语言下拉（中文/English/日本語/한국어/Français）、“开机启动”复选框、当前快捷键显示与更改、“清除浏览器缓存”按钮；保存/取消；保存后即时生效并持久化。
  - Purpose: 集中设置入口。

- [ ] 2.2 设置窗口视觉与动效（Vercel 风格 + 丰富动画）
  - Files: src/bubblebot/components/settings_window.py, src/bubblebot/logo/*
  - 与主页一致的丰富动效（淡入/缩放/悬停/按压/焦点过渡）、卡片阴影圆角、深浅色自适应，标题含 logo。
  - Purpose: 统一美学与动效体验。

- [x] 2.3 状态栏菜单精简（三项 + 动态快捷键提示）
  - File: src/bubblebot/app.py
  - 仅包含：1) 不可点击的提示项：“Press {⌘+G…} to Show/Hide”（本地化，动态刷新）；2) Settings…；3) Quit。
  - 移除：Show/Hide、Home、Set New Trigger、Clear Web Cache（迁入设置）。
  - Purpose: 菜单极简。

- [x] 2.4 将“设置快捷键”迁入设置窗口
  - Files: src/bubblebot/listener.py, src/bubblebot/components/settings_window.py
  - 捕获新组合键、冲突/非法提示、保存到既有路径。
  - Purpose: 集中配置入口。

- [ ] 3.1 移除 Autolauncher 相关代码与引用
  - Files: src/bubblebot/autolauncher.py（若有则删）, src/bubblebot/app.py（删导入/调用）, tests/ 与 README.md（删说明）
  - 检索 `Autolauncher`/`auto launch`/`Install/Uninstall` 并清理；构建/运行通过。
  - Purpose: 删除冗余实现。

- [ ] 3.2 登录项开关实现（macOS），非 Darwin 兼容
  - Files: src/bubblebot/utils/login_items.py (new), src/bubblebot/components/settings_window.py
  - ServiceManagement 开机启动；非 Darwin 提示并禁用。
  - Purpose: 跨环境兼容。

- [ ] 4.1 状态栏动态快捷键文案
  - File: src/bubblebot/app.py
  - 当前快捷键格式化为人类可读，并在设置变更时刷新提示项。
  - Purpose: 可用性。

- [ ] 5.1 测试：i18n 与设置
  - Files: tests/test_i18n.py (new), tests/test_settings.py (new)
  - 覆盖：系统语言默认、t() 回退、设置保存语言/开机启动/快捷键（Darwin mock/跳过）、状态栏提示刷新。
  - Purpose: 可靠性。

- [ ] 5.2 测试：状态栏菜单（三项 + 提示）
  - File: tests/test_status_bar.py (update/new)
  - 校验菜单仅三项，第一项不可点击且随快捷键变化，无 Home/Show/Hide/Set New Trigger/Clear Web Cache。
  - Purpose: 防回归。

- [ ] 5.3 README 重构：多语言 + Release-first
  - File: README.md
  - 顶部多语言导航；显著“Download for macOS”链接至 Releases；快速开始先推荐下载使用，再给开发运行简述；移除 Autolauncher/旧菜单说明；多语言内容结构同步。
  - Purpose: 推广与易用。

- [ ] 6.1 统一多窗口切换方法命名（保留）
  - File: src/bubblebot/components/multiwindow_manager.py
  - 将 `switchToWindow_` 重命名为 `switch_to_window_`，修正调用点。
  - Purpose: 统一命名与稳定性。

- [ ] 6.2 状态栏图标浅/深色切换健壮性（保留）
  - File: src/bubblebot/app.py
  - 校验/补充 `effectiveAppearance` 监听与 `updateStatusItemImage` 的黑/白图标切换（首帧一致、异常保护）。
  - Purpose: 可见性与一致性。
