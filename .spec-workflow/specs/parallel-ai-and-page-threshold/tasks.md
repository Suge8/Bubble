# 任务清单（Tasks）

- [x] 1. 取消 5 个页面上限（全局/单平台）
  - 文件：`src/bubblebot/models/ai_window.py`
  - 修改 `WindowManager`：
    - 将 `max_total_windows` 与 `max_windows_per_platform` 取消限制（可置为 `None` 或使用足够大的默认值并在逻辑中忽略）。
    - 在 `create_window` 与 `can_create_window` 中移除对 5 个上限的硬性判断，改为始终允许创建（仅保留必要的有效性检查）。
    - 保持现有 API 不变；更新类/方法文档说明“默认不限制数量”。
  - 目的：允许打开超过 5 个页面，不再因为上限导致“无法点击更多”。
  - 复用：现有窗口集合与构造逻辑。
  - 需求：需求 2

- [x] 2. 更新多窗口管理器以维护页面计数并对外通知
  - 文件：`src/bubblebot/components/multiwindow_manager.py`
  - 增加：
    - 属性 `on_page_count_changed: Optional[Callable[[int,int],None]]`；
    - 方法 `get_window_count() -> int`（已存在可复用）；
    - 在窗口创建成功与关闭成功后，计算旧值与新值并回调 `on_page_count_changed(old, new)`。
  - 更新类文档：移除“最多5个窗口”的描述。
  - 目的：集中维护页面计数，向上层报告跃迁事件。
  - 复用：既有窗口创建/关闭路径。
  - 需求：需求 2

- [x] 3. 在 AppDelegate 中接入计数回调并实现阈值 Toast 逻辑
  - 文件：`src/bubblebot/app.py`
  - 新增：
    - 方法 `notify_page_count_changed(old: int, new: int)`：当满足 `old < 5 and new == 5` 时触发一次 `show_toast`；当后续降到 `<5` 再升到 `==5` 时再次触发；对 `>5` 不重复提示。
    - 方法 `show_toast(text: str, duration: float = 3.0)`：轻量非阻断提示，3 秒自动消失。
  - 集成：在 `setMultiwindowManager_`（或初始化阶段已有位置）注册 `multiwindow_manager.on_page_count_changed = self.notify_page_count_changed`。
  - 移除/废弃：
    - 停用“Memory bubble”提示与“Never”按钮相关逻辑（`_ensure_memory_bubble/_update_memory_bubble_visibility/callWithSenderNever_` 等），避免与新 Toast 方案冲突；不再持久化“隐藏记忆气泡”的偏好。
  - 目的：按 4→5 跃迁弹一次 Toast，非阻断、无设置项。
  - 复用：现有 i18n 与根视图叠层容器。
  - 需求：需求 2

- [x] 4. 新增 ToastManager 工具（轻量叠层与动画）
  - 文件：`src/bubblebot/components/utils/toast_manager.py`（新建）
  - 实现：
    - `show(text: str, parent: NSView, duration: float = 3.0)`：创建圆角浅色/深色适配的提示条，淡入显示、定时淡出并移除；多次调用复用同一实例或覆盖显示。
  - 在 `AppDelegate.show_toast` 中调用该工具。
  - 目的：解耦 UI 提示实现，复用性更强。
  - 需求：需求 2

- [x] 5. 文案与本地化
  - 文件：`src/bubblebot/i18n/strings_zh.json`, `src/bubblebot/i18n/strings_en.json`
  - 新增键：`"toast.tooManyPages": "页面较多可能占用内存导致卡顿"`（中文）、`"toast.tooManyPages": "Opening many pages may cause memory usage and lag"`（英文）。
  - App 中调用 `self._i18n_or_default('toast.tooManyPages', '页面较多可能占用内存导致卡顿')`。
  - 目的：统一使用 Toast 文案，移除对“Memory bubble”文案与“Never”按钮的依赖。
  - 需求：需求 2

- [-] 6. 保证并行会话：切换焦点不销毁/重载 WebView
  - 文件：`src/bubblebot/components/multiwindow_manager.py`
  - 检查并确保：
    - 切换窗口只前置与设定焦点，不调用重载/销毁 API；
    - 关闭窗口时才释放 WebView 与 NSWindow 资源（已有 `_cleanup_window_resources` 可复用）。
  - 目的：满足并行场景下后台请求不中断。
  - 需求：需求 1

- [-] 7. 单元测试：窗口数量上限取消
  - 文件：`tests/test_window_limit.py`（新建）
  - 用例：
    - 直接实例化 `WindowManager`，循环创建 6+ 窗口，断言创建不为 `None` 且 `len(windows) >= 6`。
  - 目的：回归防止重新出现硬上限。
  - 需求：需求 2

- [-] 8. 单元测试：页面阈值 Toast 触发判定
  - 文件：`tests/test_page_threshold.py`（新建）
  - 用例：
    - 伪造 `AppDelegate`（或使用真实实例但 monkeypatch `show_toast` 计数）；
    - 模拟 `notify_page_count_changed(4,5)` 触发一次；`(5,6)` 不触发；`(6,7)` 不触发；`(4,5)` 再次触发；
    - 断言 `show_toast` 调用次数与参数正确。
  - 目的：验证 4→5 跃迁与“降到 <5 再回到 5”再次触发的逻辑。
  - 需求：需求 2

- [-] 9. 集成测试（macOS，仅在 Darwin 运行）：Toast 展现
  - 文件：`tests/test_toast_ui.py`（新建，`@skipif(platform != 'darwin')`）
  - 用例：
    - 伪造父视图，调用 `ToastManager.show`，不校验视觉，只校验不抛异常且生命周期可结束（可通过计时/回调）。
  - 目的：最低限度 UI 层健壮性验证。
  - 需求：需求 2

- [-] 10. 清理遗留与文档
  - 文件：`src/bubblebot/app.py`, `src/bubblebot/components/multiwindow_manager.py`, `src/bubblebot/models/ai_window.py`
  - 移除/更新注释中“最多5个”描述；
  - 删除/屏蔽“Memory bubble”相关 UI 与设置痕迹；
  - 目的：与新行为一致，避免二义性。
  - 需求：需求 1、需求 2
