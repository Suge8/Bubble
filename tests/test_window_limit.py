def test_window_manager_unlimited_creation():
    from bubble.models.ai_window import WindowManager, WindowType, WindowGeometry

    wm = WindowManager()
    # Ensure defaults mean unlimited
    assert wm.max_total_windows is None
    assert wm.max_windows_per_platform is None

    ids = []
    for i in range(7):
        w = wm.create_window(platform_id='openai', window_type=WindowType.MAIN, geometry=WindowGeometry())
        assert w is not None
        ids.append(w.window_id)
    assert len(wm.windows) >= 7
