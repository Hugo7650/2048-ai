// 初始化游戏棋盘
function initBoard() {
    const gameBoard = document.querySelector('.game-board');
    gameBoard.innerHTML = '';
    
    for (let i = 0; i < 4; i++) {
        for (let j = 0; j < 4; j++) {
            const cell = document.createElement('div');
            cell.className = 'cell empty';
            cell.dataset.row = i;
            cell.dataset.col = j;
            
            // 添加内容容器，便于控制内部文字样式
            const cellContent = document.createElement('div');
            cellContent.className = 'cell-content';
            cellContent.textContent = '';
            cell.appendChild(cellContent);
            
            // 桌面端事件处理
            if (!isMobileDevice()) {
                // 左键点击增加数值
                cell.addEventListener('click', () => {
                    increaseValue(i, j);
                });
                
                // 右键点击减少数值
                cell.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    decreaseValue(i, j);
                });
            } else {
                // 移动端触摸事件处理
                
                // 点击增加数值
                cell.addEventListener('click', () => {
                    increaseValue(i, j);
                });
            }
            
            gameBoard.appendChild(cell);
        }
    }
}

// 判断是否为移动设备
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// 更新游戏状态 - 修改此函数以处理手动编辑模式
function updateGameState() {
    fetch('/api/get_state')
        .then(response => response.json())
        .then(data => {
            // 更新分数
            document.getElementById('score').textContent = data.score;
            
            // 更新状态
            document.getElementById('status').textContent = data.last_move;
            
            // 更新棋盘
            updateBoard(data.board);
        });
}

// 仅更新游戏状态UI，不执行AI移动
function updateGameStateWithoutAI() {
    fetch('/api/get_state')
        .then(response => response.json())
        .then(data => {
            // 更新分数
            document.getElementById('score').textContent = data.score;
            
            // 更新状态
            document.getElementById('status').textContent = data.last_move;
            
            // 更新棋盘
            updateBoard(data.board);
        });
}

// 更新棋盘显示
function updateBoard(board) {
    const cells = document.querySelectorAll('.cell');
    
    for (let i = 0; i < 4; i++) {
        for (let j = 0; j < 4; j++) {
            const cellValue = board[i][j];
            const cellIndex = i * 4 + j;
            const cell = cells[cellIndex];
            const cellContent = cell.querySelector('.cell-content');
            
            // 更新单元格值和样式
            if (cellValue === 0) {
                cellContent.textContent = '';
                cell.className = 'cell empty';
            } else {
                cellContent.textContent = cellValue;
                cell.className = `cell tile-${cellValue}`;
                
                // 根据数字位数调整字体大小
                let sizeClass = 'size-1';
                if (cellValue >= 1000) {
                    sizeClass = 'size-3';
                } else if (cellValue >= 100) {
                    sizeClass = 'size-2';
                } else if (cellValue >= 10000) {
                    sizeClass = 'size-4';
                }
                
                cellContent.className = `cell-content ${sizeClass}`;
            }
        }
    }
}

// 增加单元格的值
function increaseValue(row, col) {
    const cells = document.querySelectorAll('.cell');
    const cellIndex = row * 4 + col;
    const cell = cells[cellIndex];
    const cellContent = cell.querySelector('.cell-content');
    
    let value = parseInt(cellContent.textContent) || 0;
    
    if (value === 0) {
        value = 2;
    } else {
        value *= 2;
    }
    
    // 发送更新请求到服务器
    fetch('/api/set_cell', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ row, col, value }),
    })
    .then(() => {
        // 仅更新UI，不触发额外的AI移动
        updateGameStateWithoutAI();
    });
}

// 减小单元格的值
function decreaseValue(row, col) {
    const cells = document.querySelectorAll('.cell');
    const cellIndex = row * 4 + col;
    const cell = cells[cellIndex];
    const cellContent = cell.querySelector('.cell-content');
    
    let value = parseInt(cellContent.textContent) || 0;
    
    if (value <= 2) {
        value = 0;
    } else {
        value /= 2;
    }
    
    // 发送更新请求到服务器
    fetch('/api/set_cell', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ row, col, value }),
    })
    .then(() => {
        // 仅更新UI，不触发额外的AI移动
        updateGameStateWithoutAI();
    });
}

// AI执行下一步
function aiMove() {
    fetch('/api/ai_move', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            alert(data.message);
        }
        // 更新游戏状态
        updateGameState();
    });
}

// 清空棋盘
function clearBoard() {
    fetch('/api/clear_board', {
        method: 'POST',
    })
    .then(() => {
        // 更新游戏状态
        updateGameState();
    });
}

// 生成随机棋盘
function randomBoard() {
    fetch('/api/random_board', {
        method: 'POST',
    })
    .then(() => {
        // 更新游戏状态
        updateGameState();
    });
}

// 初始化触摸事件处理
function initTouchEvents() {
    // 在移动设备上设置长按处理
    if (isMobileDevice()) {
        // 更新单元格的长按处理
        const cells = document.querySelectorAll('.cell');
        cells.forEach(cell => {
            const row = parseInt(cell.dataset.row);
            const col = parseInt(cell.dataset.col);
            
            let longPressTimer;
            
            cell.addEventListener('touchstart', (e) => {
                longPressTimer = setTimeout(() => {
                    decreaseValue(row, col);
                }, 500); // 500ms长按触发
            });
            
            cell.addEventListener('touchend', () => {
                clearTimeout(longPressTimer);
            });
            
            cell.addEventListener('touchmove', () => {
                clearTimeout(longPressTimer);
            });
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化棋盘
    initBoard();
    
    // 初始化触摸事件
    initTouchEvents();
    
    // 获取初始游戏状态
    updateGameState();
    
    // 添加按钮事件监听
    document.getElementById('ai-move-btn').addEventListener('click', aiMove);
    document.getElementById('clear-board-btn').addEventListener('click', clearBoard);
    document.getElementById('random-board-btn').addEventListener('click', randomBoard);
    
    // 添加方向按钮事件处理
    document.getElementById('dir-up')?.addEventListener('click', () => {
        fetch('/api/execute_direction', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move: 0 })
        }).then(() => updateGameState());
    });
    
    document.getElementById('dir-down')?.addEventListener('click', () => {
        fetch('/api/execute_direction', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move: 1 })
        }).then(() => updateGameState());
    });
    
    document.getElementById('dir-left')?.addEventListener('click', () => {
        fetch('/api/execute_direction', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move: 2 })
        }).then(() => updateGameState());
    });
    
    document.getElementById('dir-right')?.addEventListener('click', () => {
        fetch('/api/execute_direction', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move: 3 })
        }).then(() => updateGameState());
    });
    
    // 设置键盘方向键控制
    document.addEventListener('keydown', (e) => {
        switch(e.key) {
            case 'ArrowUp':
                fetch('/api/execute_direction', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ move: 0 })
                }).then(() => updateGameState());
                break;
            case 'ArrowDown':
                fetch('/api/execute_direction', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ move: 1 })
                }).then(() => updateGameState());
                break;
            case 'ArrowLeft':
                fetch('/api/execute_direction', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ move: 2 })
                }).then(() => updateGameState());
                break;
            case 'ArrowRight':
                fetch('/api/execute_direction', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ move: 3 })
                }).then(() => updateGameState());
                break;
        }
    });
    
    // 设置定期更新游戏状态，但不触发AI
    setInterval(updateGameStateWithoutAI, 1000);
});
