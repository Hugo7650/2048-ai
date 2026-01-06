from flask import Flask, render_template, jsonify, request
import numpy as np
import json
import os
from threading import Thread
import webbrowser
from ailib import to_c_board, from_c_board, from_c_index, ailib

app = Flask(__name__, 
           static_folder='web/static',
           template_folder='web/templates')

# 全局游戏状态
game_state = {
    "board": [[0 for _ in range(4)] for _ in range(4)],
    "score": 0,
    "last_move": "等待操作",
    "manual_edit": False  # 新增标记，指示是否正在手动编辑
}

# 游戏控制器实例，将在主程序中初始化
game_controller = None

class WebGameControl:
    """为主程序提供的Web游戏控制接口"""
    
    def __init__(self, ai_solver_func):
        self.ai_solver_func = ai_solver_func
        from ailib import ailib
        self.ailib = ailib
    
    def get_status(self):
        """始终返回'running'状态以保持游戏进行"""
        return 'running'
    
    def get_score(self):
        """获取当前分数"""
        return game_state["score"]
    
    def get_board(self):
        """获取当前棋盘状态，返回对数形式的棋盘"""
        board = game_state["board"]
        # 直接返回棋盘的对数形式
        return [[int(np.log2(max(tile, 1))) for tile in row] for row in board]
    
    def execute_move(self, move):
        """使用C接口执行移动"""
        # 重置手动编辑标记
        game_state["manual_edit"] = False
        
        # 将当前棋盘转换为C接口可用格式
        c_board = to_c_board(self.get_board())
        # 使用C接口执行移动
        new_c_board = self.ailib.execute_move(move, c_board)
        # 将结果转换回Python格式
        new_board = from_c_board(new_c_board)
        
        # 检查棋盘是否有变化
        board_changed = False
        orig_board = self.get_board()
        for i in range(4):
            for j in range(4):
                if new_board[i][j] != orig_board[i][j]:
                    board_changed = True
                    break
            if board_changed:
                break
        
        if board_changed:
            # 更新棋盘
            for i in range(4):
                for j in range(4):
                    if new_board[i][j] > 0:
                        game_state["board"][i][j] = 2 ** new_board[i][j]
                    else:
                        game_state["board"][i][j] = 0
            
            # 添加新方块
            # self._add_new_tile()
            
            # 计算得分差异并更新分数
            score_increase = 0
            for i in range(4):
                for j in range(4):
                    if new_board[i][j] > orig_board[i][j] and orig_board[i][j] > 0:
                        # 有合并发生
                        score_increase += 2 ** new_board[i][j]
            
            game_state["score"] += score_increase
            
            # 更新最后一步
            move_names = ['上移', '下移', '左移', '右移']
            game_state["last_move"] = f"上一步: {move_names[move]}"
    
    def restart_game(self):
        """重新开始游戏"""
        self._clear_board()
    
    def continue_game(self):
        """继续游戏"""
        pass
    
    def setup_web(self, port=5000):
        """设置并启动Web服务器"""
        global game_controller
        game_controller = self
        
        # 创建必要的目录结构
        self._ensure_directories()
        
        # 在新线程中启动Flask服务器
        def run_server():
            app.run(host='0.0.0.0', port=port, debug=False)  # 使用0.0.0.0允许外部设备访问
        
        server_thread = Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # 打开浏览器
        webbrowser.open(f'http://127.0.0.1:{port}')
        
        # 输出访问信息
        print(f"Web服务器已启动，可通过以下地址访问:")
        print(f" - 本机: http://127.0.0.1:{port}")
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f" - 局域网: http://{local_ip}:{port}")
        except:
            pass
        
        # 保持主线程运行
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("Web服务器已关闭")
    
    def _ensure_directories(self):
        """确保所需的目录结构存在"""
        dirs = [
            'web/templates',
            'web/static/css',
            'web/static/js'
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def _clear_board(self):
        """清空棋盘"""
        game_state["board"] = [[0 for _ in range(4)] for _ in range(4)]
        game_state["score"] = 0
        game_state["last_move"] = "等待操作"
        game_state["manual_edit"] = False  # 重置手动编辑标记
    
    def _add_new_tile(self):
        """在随机空位添加一个新的2或4方块"""
        # 找到所有空位
        empty_cells = [(i, j) for i in range(4) for j in range(4) if game_state["board"][i][j] == 0]
        
        if empty_cells:
            # 随机选择一个空位
            i, j = empty_cells[np.random.randint(0, len(empty_cells))]
            # 90%概率为2，10%概率为4
            game_state["board"][i][j] = 2 if np.random.random() < 0.9 else 4

# Flask路由

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/get_state')
def get_state():
    """获取当前游戏状态"""
    return jsonify(game_state)

@app.route('/api/clear_board', methods=['POST'])
def clear_board():
    """清空棋盘"""
    if game_controller:
        game_controller._clear_board()
    return jsonify({"status": "success"})

@app.route('/api/random_board', methods=['POST'])
def random_board():
    """生成随机棋盘"""
    if game_controller:
        # 清空棋盘
        game_controller._clear_board()
        
        # 放置8-12个非零方块
        num_tiles = np.random.randint(8, 13)
        available_positions = [(i, j) for i in range(4) for j in range(4)]
        np.random.shuffle(available_positions)
        
        for k in range(min(num_tiles, len(available_positions))):
            i, j = available_positions[k]
            # 生成2的幂次方（2到2048）
            power = np.random.randint(1, 11)  # 1到10之间的随机数
            game_state["board"][i][j] = 2 ** power
        
        # 重置手动编辑标记
        game_state["manual_edit"] = False
        game_state["last_move"] = "随机棋盘"
    
    return jsonify({"status": "success"})

@app.route('/api/set_cell', methods=['POST'])
def set_cell():
    """设置特定单元格的值"""
    data = request.json
    i, j, value = data['row'], data['col'], data['value']
    
    # 确保索引在有效范围内
    if 0 <= i < 4 and 0 <= j < 4:
        # 设置手动编辑标记
        game_state["manual_edit"] = True
        game_state["board"][i][j] = value
        game_state["last_move"] = "手动编辑"
    
    return jsonify({"status": "success"})

@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    """AI执行下一步"""
    if game_controller and game_controller.ai_solver_func:
        # 重置手动编辑标记
        game_state["manual_edit"] = False
        
        # 获取AI的最佳移动
        board = game_controller.get_board()
        move = game_controller.ai_solver_func(board)
        
        if move >= 0:
            # 执行移动
            game_controller.execute_move(move)
            return jsonify({"status": "success", "move": move})
        else:
            return jsonify({"status": "error", "message": "当前局面没有可行的移动"})
    
    return jsonify({"status": "error", "message": "AI未初始化"})

@app.route('/api/execute_direction', methods=['POST'])
def execute_direction():
    """根据指定方向执行移动"""
    if game_controller:
        # 重置手动编辑标记
        game_state["manual_edit"] = False
        
        data = request.json
        move = data.get('move', -1)
        
        if 0 <= move < 4:
            board = game_controller.get_board()
            # 检查指定方向是否是有效移动
            c_board = to_c_board(board)
            new_c_board = ailib.execute_move(move, c_board)
            
            # 如果棋盘发生变化，则为有效移动
            if c_board != new_c_board:
                game_controller.execute_move(move)
                return jsonify({"status": "success", "move": move})
            else:
                return jsonify({"status": "error", "message": "该方向无法移动"})
    
    return jsonify({"status": "error", "message": "操作失败"})

if __name__ == "__main__":
    # 直接运行此文件时的测试代码
    from ailib import find_best_move
    ctrl = WebGameControl(find_best_move)
    ctrl.setup_web()
