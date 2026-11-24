"""PySide6 (Qt) 交互视图与状态机单元测试（离屏模式）。"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from main import BFS_SOLVERS, DFS_SOLVERS, GENERATORS, carve_demo_maze
from maze.model import E, Maze, S, SolveResult, W
from maze.render import qt_view


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_manual_walk_state_blocks_wall_and_tracks_backtrack():
    maze = carve_demo_maze()
    state = qt_view.ManualWalkState(maze)
    assert state.pos == (0, 0)
    assert state.steps == 0

    # (0,0) 下方有墙，不能走
    assert not state.move(S)
    assert state.pos == (0, 0)
    assert state.steps == 0

    # (0,0) 右侧是通的
    assert state.move(E)
    assert state.pos == (0, 1)
    assert state.steps == 1
    assert state.trail == [(0, 0), (0, 1)]

    # 往回退到 (0,0)，轨迹应弹出最后一格，但步数累加
    assert state.move(W)
    assert state.pos == (0, 0)
    assert state.steps == 2
    assert state.trail == [(0, 0)]

    state.reset()
    assert state.pos == (0, 0)
    assert state.steps == 0
    assert state.trail == [(0, 0)]
    assert not state.reached_end


def test_manual_walk_state_reaches_end():
    maze = carve_demo_maze()
    state = qt_view.ManualWalkState(maze)
    # 沿蛇形走廊走到默认终点 (5,5)
    moves = [E] * 5 + [S, S] + [W] * 5 + [S, S] + [E] * 5 + [S]
    for d in moves:
        assert state.move(d)
    assert state.pos == maze.end
    assert state.reached_end


def test_step_timeline_snapshots_and_bounds():
    res = SolveResult(
        path=[(0, 0), (0, 1), (1, 1)],
        visited_order=[(0, 0), (0, 1), (1, 0), (1, 1)],
        found=True,
        expanded=4,
    )
    tl = qt_view.StepTimeline(res)
    assert tl.total_steps == 7

    s0 = tl.snapshot(-5)
    assert s0.clamped_step == 0
    assert s0.visited_count == 0
    assert s0.path_count == 0
    assert s0.current_cell is None
    assert s0.phase == "未开始"

    s1 = tl.snapshot(1)
    assert s1.visited_count == 1
    assert s1.path_count == 0
    assert s1.current_cell == (0, 0)
    assert s1.phase == "搜索中"

    s4 = tl.snapshot(4)
    assert s4.visited_count == 4
    assert s4.path_count == 0
    assert s4.current_cell == (1, 1)
    assert s4.phase == "搜索中"

    s5 = tl.snapshot(5)
    assert s5.visited_count == 4
    assert s5.path_count == 1
    assert s5.current_cell == (0, 0)
    assert s5.phase == "回溯路径"

    s_end = tl.snapshot(99)
    assert s_end.clamped_step == 7
    assert s_end.visited_count == 4
    assert s_end.path_count == 3
    assert s_end.current_cell == (1, 1)
    assert s_end.phase == "已完成"


def test_startup_dialog_config():
    _get_app()
    dlg = qt_view.StartupDialog(
        GENERATORS,
        initial_rows=10,
        initial_cols=12,
        initial_gen="prim",
    )
    assert dlg.get_config() == (10, 12, "prim")

    dlg.rows_spin.setValue(20)
    dlg.cols_spin.setValue(25)
    dlg.gen_combo.setCurrentIndex(0)
    dlg.loop_spin.setValue(15)
    dlg.mud_spin.setValue(25)
    assert dlg.get_config() == (20, 25, "kruskal")
    assert dlg.get_full_config() == (20, 25, "kruskal", 0.15, 0.25)
    dlg.close()


def test_main_window_manual_and_compare_keyboard_stepping():
    _get_app()
    maze = carve_demo_maze()
    win = qt_view.MazeMainWindow(
        maze,
        "kruskal",
        GENERATORS,
        BFS_SOLVERS,
        DFS_SOLVERS,
    )
    try:
        # 1. 手动模式方向键移动
        ev_right = QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier)
        win.keyPressEvent(ev_right)
        assert win._walk_state.pos == (0, 1)
        assert win._walk_state.steps == 1

        # 2. 切换至“让程序走（BFS vs DFS 对比）”模式
        win.switch_mode(1)
        assert win.bfs_canvas._maze is win._maze
        assert win.dfs_canvas._maze is win._maze
        assert win._cur_step == 0
        assert win._max_step > 0

        # 方向键前进一步与回退一步
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))
        assert win._cur_step == 1
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier))
        assert win._cur_step == 2
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.NoModifier))
        assert win._cur_step == 1
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier))
        assert win._cur_step == 0

        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_End, Qt.NoModifier))
        assert win._cur_step == win._max_step
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Home, Qt.NoModifier))
        assert win._cur_step == 0

        # 切换算法版本后正常重算
        win.bfs_combo.setCurrentIndex(1)
        win.dfs_combo.setCurrentIndex(1)
        assert win._cur_step == 0
        assert win._max_step > 0

        # 离屏绘制截图不崩溃
        win.resize(900, 600)
        pixmap = win.grab()
        assert not pixmap.isNull()
    finally:
        win.close()


def test_step_timeline_and_canvas_backtrack_animation():
    """验证含 backtrack 事件的 trace 在前进/回退与离屏渲染时状态准确。"""
    _get_app()
    maze = Maze(2, 3)
    maze.remove_wall_between((0, 0), (0, 1))
    maze.remove_wall_between((0, 1), (0, 2))
    maze.remove_wall_between((0, 0), (1, 0))
    maze.remove_wall_between((1, 0), (1, 1))
    maze.remove_wall_between((1, 1), (1, 2))

    # 使用默认第一项（递归版 DFS）
    _, _, dfs_rec_fn = DFS_SOLVERS[0]
    res = dfs_rec_fn(maze)
    tl = qt_view.StepTimeline(res)
    assert tl.use_trace
    assert tl.search_total == len(res.trace)

    # 第 3 步走到死胡同尽头 (0,2)，活跃栈为 [(0,0), (0,1), (0,2)]
    s3 = tl.snapshot(3)
    assert s3.phase == "搜索中"
    assert s3.active_stack == ((0, 0), (0, 1), (0, 2))
    assert s3.backtracked_cells == frozenset()

    # 第 4 步触发首次回溯 ("backtrack", (0,2))
    s4 = tl.snapshot(4)
    assert s4.phase == "死路回溯"
    assert s4.current_action == "backtrack"
    assert s4.current_cell == (0, 2)
    assert s4.backtracked_cells == frozenset({(0, 2)})
    assert s4.active_stack == ((0, 0), (0, 1))
    assert s4.backtrack_count == 1

    # 第 5 步继续回溯 ("backtrack", (0,1))
    s5 = tl.snapshot(5)
    assert s5.phase == "死路回溯"
    assert s5.backtracked_cells == frozenset({(0, 2), (0, 1)})
    assert s5.active_stack == ((0, 0),)
    assert s5.backtrack_count == 2

    # 在离屏画布中渲染正在回溯的那一帧
    canvas = qt_view.MazeCanvas()
    canvas.resize(360, 260)
    canvas.set_solver_state(maze, res, 4)
    pix = canvas.grab()
    assert not pix.isNull()
    canvas.close()


def test_generation_timeline_and_canvas_animation():
    """验证迷宫生成动画时间线的逐步拆墙、回退恢复墙面及方向键控制。"""
    _get_app()
    maze = Maze.generate(4, 5, method="prim")
    tl = qt_view.GenerationTimeline(maze)
    assert tl.total_steps == 4 * 5 - 1

    # 第 0 步：四面全墙、尚未开始
    s0 = tl.snapshot(0)
    assert s0.phase == "未开始"
    assert s0.last_edge is None
    assert s0.carved_cells == frozenset()
    assert all(cell == 15 for row in s0.maze.walls for cell in row)

    # 第 1 步与第 2 步：记录刚打通的相邻格对
    s1 = tl.snapshot(1)
    assert s1.phase == "生成中"
    assert s1.last_edge == maze.carve_history[0]
    assert set(s1.last_edge).issubset(s1.carved_cells)

    s2 = tl.snapshot(2)
    assert s2.last_edge == maze.carve_history[1]
    assert s2.recent_edges == tuple(maze.carve_history[:2])

    # 在离屏画布上渲染拆墙中间过渡帧 (anim_t=0.45)，验证双开门收缩、光晕与火花渲染正常
    canvas = qt_view.MazeCanvas()
    canvas.resize(360, 260)
    canvas.set_generation_state(tl, 2, anim_t=0.45)
    mid_pix = canvas.grab()
    assert not mid_pix.isNull()
    canvas.close()

    # 回退到第 1 步，应恢复第 2 步拆掉的墙且与之前 s1 完全一致
    s1_back = tl.snapshot(1)
    assert s1_back.maze.walls == s1.maze.walls
    assert s1_back.carved_cells == s1.carved_cells

    # 终点步应还原出与目标迷宫完全一致的墙位
    s_end = tl.snapshot(tl.total_steps)
    assert s_end.phase == "已完成"
    assert s_end.maze.walls == maze.walls

    # 测试主窗口生成动画页的方向键前进/回退与离屏绘制
    win = qt_view.MazeMainWindow(maze, "prim", GENERATORS, BFS_SOLVERS, DFS_SOLVERS)
    try:
        win.switch_mode(2)
        assert win._gen_step == 0
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))
        assert win._gen_step == 1
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier))
        assert win._gen_step == 2
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.NoModifier))
        assert win._gen_step == 1
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_End, Qt.NoModifier))
        assert win._gen_step == win._gen_max_step
        win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Home, Qt.NoModifier))
        assert win._gen_step == 0

        win.resize(800, 600)
        pix = win.grab()
        assert not pix.isNull()
    finally:
        win.close()


def test_division_wall_building_and_weighted_mud_rendering():
    """验证递归分割法筑墙动画、泥地地形绘制及 A* vs Dijkstra 同屏切换。"""
    _get_app()
    maze = Maze.generate(6, 7, method="division", loop_ratio=0.15, mud_ratio=0.3)
    tl = qt_view.GenerationTimeline(maze)
    assert tl.total_steps == len(maze.gen_steps)

    s0 = tl.snapshot(0)
    assert s0.maze.initial_open
    assert s0.last_action == "add"

    s1 = tl.snapshot(1)
    assert s1.last_action == "add"

    s_end = tl.snapshot(tl.total_steps)
    assert s_end.phase == "已完成"
    assert s_end.maze.walls == maze.walls

    # 离屏渲染递归分割筑墙动画过渡帧
    canvas = qt_view.MazeCanvas()
    canvas.resize(400, 320)
    canvas.set_generation_state(tl, 1, anim_t=0.45)
    div_pix = canvas.grab()
    assert not div_pix.isNull()
    canvas.close()

    # 主窗口对比页切换到 A* vs Dijkstra（含泥地渲染）
    win = qt_view.MazeMainWindow(
        maze,
        "division",
        GENERATORS,
        BFS_SOLVERS,
        DFS_SOLVERS,
        loop_ratio=0.15,
        mud_ratio=0.3,
    )
    try:
        win.switch_mode(1)
        astar_idx = win.bfs_combo.findData("astar")
        dijk_idx = win.dfs_combo.findData("dijkstra")
        assert astar_idx >= 0 and dijk_idx >= 0
        win.bfs_combo.setCurrentIndex(astar_idx)
        win.dfs_combo.setCurrentIndex(dijk_idx)
        assert win._bfs_result.cost == win._dfs_result.cost
        win.resize(960, 640)
        pix = win.grab()
        assert not pix.isNull()
    finally:
        win.close()


def test_qt_view_decoupled_from_algorithms():
    src = (Path(__file__).resolve().parent.parent / "maze" / "render" / "qt_view.py").read_text(
        encoding="utf-8"
    )
    assert "maze.generators" not in src
    assert "maze.solvers" not in src
