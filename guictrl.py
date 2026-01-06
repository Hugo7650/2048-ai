import tkinter as tk
from tkinter import messagebox, font
import numpy as np
from ailib import to_c_board, from_c_board, from_c_index, ailib
from functools import lru_cache

# 使用缓存装饰器避免重复计算颜色值
@lru_cache(maxsize=32)
def get_tile_color(value):
    """根据方块值返回背景色和文字色"""
    if value == 0:
        return "#ccc0b3", "#776e65"  # 空方块
    elif value == 2:
        return "#eee4da", "#776e65"
    elif value == 4:
        return "#ede0c8", "#776e65"
    elif value == 8:
        return "#f2b179", "#f9f6f2"
    elif value == 16:
        return "#f59563", "#f9f6f2"
    elif value == 32:
        return "#f67c5f", "#f9f6f2"
    elif value == 64:
        return "#f65e3b", "#f9f6f2"
    elif value == 128:
        return "#edcf72", "#f9f6f2"
    elif value == 256:
        return "#edcc61", "#f9f6f2"
    elif value == 512:
        return "#edc850", "#f9f6f2"
    elif value == 1024:
        return "#edc53f", "#f9f6f2"
    elif value == 2048:
        return "#edc22e", "#f9f6f2"
    else:
        return "#3c3a32", "#f9f6f2"  # 更高的值

class GUI2048Control:
    """GUI控制界面，可以手动设置局面并让AI执行下一步"""
    
    def __init__(self, ai_solver_func):
        self.ai_solver_func = ai_solver_func
        self.window = tk.Tk()
        self.window.title("2048 AI 控制界面")
        self.window.geometry("600x650")
        self.window.resizable(False, False)
        
        # 设置更适合中文显示的默认字体
        self.default_font = ("Microsoft YaHei UI", 12)  # 微软雅黑UI字体
        self.title_font = ("Microsoft YaHei UI", 14, "bold")
        self.number_font = ("Arial", 24, "bold")  # 数字仍然使用Arial字体
        
        self.board = [[0 for _ in range(4)] for _ in range(4)]
        self.cells = []
        self.score = 0
        
        self._initialize_ui()
    
    def _initialize_ui(self):
        # 设置顶部信息区域
        info_frame = tk.Frame(self.window)
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text="分数:", font=self.title_font).grid(row=0, column=0, padx=10)
        self.score_label = tk.Label(info_frame, text="0", font=self.title_font)
        self.score_label.grid(row=0, column=1, padx=10)
        
        # 添加上一步移动的标签
        tk.Label(info_frame, text="状态:", font=self.title_font).grid(row=0, column=2, padx=10)
        self.last_move_label = tk.Label(info_frame, text="等待操作", font=self.title_font)
        self.last_move_label.grid(row=0, column=3, padx=10)
        
        # 设置游戏棋盘区域
        game_frame = tk.Frame(self.window, bg="#bbada0", padx=10, pady=10)
        game_frame.pack(pady=10)
        
        for i in range(4):
            row = []
            for j in range(4):
                cell_frame = tk.Frame(game_frame, width=100, height=100, bg="#ccc0b3")
                cell_frame.grid(row=i, column=j, padx=5, pady=5)
                cell_frame.grid_propagate(False)
                
                cell_value = tk.Label(cell_frame, text="", font=self.number_font, bg="#ccc0b3")
                cell_value.place(relx=0.5, rely=0.5, anchor="center")
                
                # 替换点击事件：左键增大，右键减小
                cell_frame.bind("<Button-1>", lambda event, i=i, j=j: self._increase_value(i, j))
                cell_value.bind("<Button-1>", lambda event, i=i, j=j: self._increase_value(i, j))
                cell_frame.bind("<Button-3>", lambda event, i=i, j=j: self._decrease_value(i, j))
                cell_value.bind("<Button-3>", lambda event, i=i, j=j: self._decrease_value(i, j))
                
                row.append(cell_value)
            self.cells.append(row)
        
        # 添加操作提示
        hint_frame = tk.Frame(self.window)
        hint_frame.pack(pady=5)
        tk.Label(hint_frame, text="左键点击增大数值，右键点击减小数值", font=self.default_font).pack()
        
        # 设置控制按钮区域
        control_frame = tk.Frame(self.window)
        control_frame.pack(pady=20)
        
        # 使用更适合中文的按钮样式
        button_style = {"font": self.default_font, "padx": 5, "pady": 5, "width": 10, "relief": tk.RAISED}
        
        tk.Button(control_frame, text="AI下一步", command=self._ai_next_move, 
                  **button_style).grid(row=0, column=0, padx=15)
        tk.Button(control_frame, text="清空棋盘", command=self._clear_board, 
                  **button_style).grid(row=0, column=1, padx=15)
        tk.Button(control_frame, text="随机棋盘", command=self._random_board, 
                  **button_style).grid(row=0, column=2, padx=15)
    
    def _increase_value(self, i, j):
        """增大单元格的值"""
        current = self.board[i][j]
        if current == 0:
            self.board[i][j] = 2
        else:
            self.board[i][j] = current * 2
        # 只更新修改的单元格而不是整个棋盘
        self._update_cell(i, j)
    
    def _decrease_value(self, i, j):
        """减小单元格的值"""
        current = self.board[i][j]
        if current <= 2:
            self.board[i][j] = 0
        else:
            self.board[i][j] = current // 2
        # 只更新修改的单元格而不是整个棋盘
        self._update_cell(i, j)
    
    def _update_cell(self, i, j):
        """更新单个单元格的显示"""
        value = self.board[i][j]
        if value == 0:
            self.cells[i][j].configure(text="", bg="#ccc0b3")
            self.cells[i][j].master.configure(bg="#ccc0b3")
        else:
            self.cells[i][j].configure(text=str(value))
            bg_color, text_color = get_tile_color(value)
            self.cells[i][j].configure(bg=bg_color, fg=text_color)
            self.cells[i][j].master.configure(bg=bg_color)
            
            # 根据数字位数调整字体大小
            if value < 100:
                font_size = 24
            elif value < 1000:
                font_size = 20
            elif value < 10000:
                font_size = 16
            else:
                font_size = 14
                
            self.cells[i][j].configure(font=("Arial", font_size, "bold"))
    
    def _update_display(self):
        """更新界面显示"""
        for i in range(4):
            for j in range(4):
                self._update_cell(i, j)
    
    def _clear_board(self):
        """清空棋盘"""
        self.board = [[0 for _ in range(4)] for _ in range(4)]
        self.score = 0
        self.score_label.configure(text="0")
        self._update_display()
    
    def _random_board(self):
        """生成随机棋盘"""
        self._clear_board()
        # 放置8-12个非零方块
        num_tiles = np.random.randint(8, 13)
        available_positions = [(i, j) for i in range(4) for j in range(4)]
        np.random.shuffle(available_positions)
        
        for k in range(min(num_tiles, len(available_positions))):
            i, j = available_positions[k]
            # 生成2的幂次方（2到2048）
            power = np.random.randint(1, 11)  # 1到10之间的随机数
            self.board[i][j] = 2 ** power
        
        self._update_display()
    
    def _ai_next_move(self):
        """AI执行下一步"""
        # 检查棋盘是否有足够的方块
        if not any(any(row) for row in self.board):
            messagebox.showinfo("提示", "请先设置棋盘", font=self.default_font)
            return
        
        # 将棋盘转换为AI可用的格式 - 使用列表推导式优化
        log2_board = [[int(np.log2(max(tile, 1))) for tile in row] for row in self.board]
        
        # 获取AI的最佳移动
        move = self.ai_solver_func(log2_board)
        if move < 0:
            messagebox.showinfo("AI分析", "当前局面没有可行的移动")
            return
        
        # 执行移动而不是显示建议
        move_names = ['上移', '下移', '左移', '右移']
        self._execute_move(move)
        
        # 更新状态栏显示最后执行的移动
        self.last_move_label.configure(text=f"上一步: {move_names[move]}")
    
    def _execute_move(self, direction):
        """执行移动操作，使用C接口"""
        # 将当前棋盘转换为C接口可用格式
        log2_board = [[int(np.log2(max(tile, 1))) for tile in row] for row in self.board]
        c_board = to_c_board(log2_board)
        
        # 使用C接口执行移动
        new_c_board = ailib.execute_move(direction, c_board)
        
        # 将结果转换回Python格式
        new_board = from_c_board(new_c_board)
        
        # 检查棋盘是否有变化
        board_changed = False
        for i in range(4):
            for j in range(4):
                if new_board[i][j] != log2_board[i][j]:
                    board_changed = True
                    break
            if board_changed:
                break
                
        if board_changed:
            # 更新棋盘
            for i in range(4):
                for j in range(4):
                    if new_board[i][j] > 0:
                        self.board[i][j] = 2 ** new_board[i][j]
                    else:
                        self.board[i][j] = 0
                        
            # 添加新方块
            # self._add_new_tile()
            
            # 计算得分差异并更新分数
            # 这里简化处理，直接从UI中读取分数不太可能，所以计算合并格子产生的分数
            old_sum = sum(sum(log2_board, []))
            new_sum = sum(sum(new_board, []))
            # 差值中不包括新增的方块(通常为1或2)
            score_increase = 0
            for i in range(4):
                for j in range(4):
                    if new_board[i][j] > log2_board[i][j] and log2_board[i][j] > 0:
                        # 有合并发生
                        score_increase += 2 ** new_board[i][j]
            
            self.score += score_increase
            self.score_label.configure(text=str(self.score))
            
            # 更新界面显示
            self._update_display()
    
    def _add_new_tile(self):
        """在随机空位添加一个新的2或4方块"""
        # 找到所有空位 - 使用列表推导式
        empty_cells = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        
        if empty_cells:
            # 随机选择一个空位
            i, j = empty_cells[np.random.randint(0, len(empty_cells))]
            # 90%概率为2，10%概率为4
            self.board[i][j] = 2 if np.random.random() < 0.9 else 4
    
    def run(self):
        """运行GUI"""
        # 设置消息框的默认字体
        self.window.option_add('*Dialog.msg.font', self.default_font)
        self.window.option_add('*Dialog.msg.width', 10)
        
        # 启动主循环
        self.window.mainloop()

class GUIGameControl:
    """为主程序提供的游戏控制接口"""
    
    def __init__(self, ai_solver_func):
        self.ai_solver_func = ai_solver_func
        self.gui = None
        from ailib import ailib
        self.ailib = ailib
    
    def get_status(self):
        """始终返回'running'状态以保持游戏进行"""
        return 'running'
    
    def get_score(self):
        """获取当前分数"""
        if self.gui:
            return int(self.gui.score)
        return 0
    
    def get_board(self):
        """获取当前棋盘状态"""
        if self.gui:
            # 直接返回棋盘的对数形式
            return [[int(np.log2(max(tile, 1))) for tile in row] for row in self.gui.board]
        return [[0 for _ in range(4)] for _ in range(4)]
    
    def execute_move(self, move):
        """使用C接口执行移动"""
        if self.gui:
            # 将当前棋盘转换为C接口可用格式
            from ailib import to_c_board, from_c_board
            c_board = to_c_board(self.get_board())
            # 使用C接口执行移动
            new_c_board = self.ailib.execute_move(move, c_board)
            # 将结果转换回Python格式
            new_board = from_c_board(new_c_board)
            # 将对数形式转换回原始值
            for i in range(4):
                for j in range(4):
                    if new_board[i][j] > 0:
                        self.gui.board[i][j] = 2 ** new_board[i][j]
                    else:
                        self.gui.board[i][j] = 0
            # 更新界面
            self.gui._update_display()
            # 更新状态标签
            move_names = ['上移', '下移', '左移', '右移']
            self.gui.last_move_label.configure(text=f"上一步: {move_names[move]}")
    
    def restart_game(self):
        """重新开始游戏"""
        if self.gui:
            self.gui._clear_board()
    
    def continue_game(self):
        """继续游戏"""
        pass
    
    def setup_gui(self):
        """设置并启动GUI"""
        self.gui = GUI2048Control(self.ai_solver_func)
        self.gui.run()
