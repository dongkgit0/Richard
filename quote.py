import random
import tkinter as tk

quotes = [
    "人生不是坐等风暴过去，而是学会在雨中跳舞。",
    "你只管努力，剩下的交给时间。",
    "代码改变世界。",
    "坚持就是胜利。"
]
quote = random.choice(quotes)

# 窗口基础设置
root = tk.Tk()
root.title("今日暖心便签")
root.geometry("380x380")
root.resizable(0, 0)

# 底层画布做烟花粒子背景
canvas = tk.Canvas(root, width=380, height=380, bg="#FFF2CC", highlightthickness=0)
canvas.place(x=0, y=0)

fireworks = []

# 生成少量暖色烟花粒子
def create_firework():
    # 单次只生成少量粒子
    for _ in range(random.randint(2, 4)):
        x = random.randint(10, 370)
        y = random.randint(10, 370)
        # 暖色系配色
        color = random.choice([
            "#FFCC80", "#FFB347", "#FFA500", "#FFD700",
            "#FFE4B5", "#FFDF99", "#F9BC60", "#FFC960"
        ])
        size = random.randint(1, 4)
        vx = random.uniform(-1.8, 1.8)
        vy = random.uniform(-1.8, 1.8)
        life = random.randint(40, 70)
        particle = canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline="")
        fireworks.append([particle, vx, vy, life])

# 粒子动画更新
def update_firework():
    # 降低生成频率，背景稀疏柔和
    if random.random() < 0.12:
        create_firework()

    new_fw = []
    for item in fireworks:
        pid, vx, vy, life = item
        canvas.move(pid, vx, vy)
        life -= 1
        if life > 0:
            new_fw.append([pid, vx, vy, life])
        else:
            canvas.delete(pid)
    fireworks[:] = new_fw
    root.after(45, update_firework)

# 启动粒子动画
update_firework()

# 标题文字（顶层，不会被粒子遮挡）
title_label = tk.Label(
    root,
    text="✨ 今日名言",
    font=("微软雅黑", 14, "bold"),
    bg="#FFF2CC",
    fg="#E67700"
)
title_label.pack(pady=30)

# 名言正文
text_label = tk.Label(
    root,
    text=quote,
    font=("微软雅黑", 14),
    bg="#FFF2CC",
    fg="#995500",
    wraplength=330,
    justify="center"
)
text_label.pack(pady=20)

# 窗口居中
root.eval('tk::PlaceWindow . center')
root.mainloop()