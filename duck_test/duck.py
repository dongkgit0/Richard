from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 三种小黄鸭性格定义
duck_personality = {
    "sunny": {
        "name": "阳光开朗鸭",
        "emoji": "☀️",
        "desc": "你热情乐观、充满活力，像小太阳一样温暖身边所有人，走到哪里都自带快乐光环！",
        "color": "#FFE066"
    },
    "quiet": {
        "name": "温柔治愈鸭",
        "emoji": "🌿",
        "desc": "你温柔内敛、心思细腻，喜欢安静舒适的小世界，是身边人最靠谱的治愈小港湾～",
        "color": "#A8E6CF"
    },
    "brave": {
        "name": "勇敢冒险鸭",
        "emoji": "🚀",
        "desc": "你勇敢无畏、好奇心爆棚，喜欢探索新鲜事物，永远对世界充满冲劲和期待！",
        "color": "#FFB3BA"
    }
}

# 测试题目
questions = [
    {
        "id": 1,
        "title": "周末你更想怎么度过？",
        "options": [
            {"text": "和朋友出门玩耍、打卡新地方", "type": "sunny"},
            {"text": "宅家看书、晒太阳、发呆", "type": "quiet"},
            {"text": "去户外探险/尝试新运动", "type": "brave"}
        ]
    },
    {
        "id": 2,
        "title": "朋友不开心时，你会？",
        "options": [
            {"text": "讲笑话逗他开心，活力满满", "type": "sunny"},
            {"text": "安静陪伴，温柔倾听", "type": "quiet"},
            {"text": "带他出门散心，解决问题", "type": "brave"}
        ]
    },
    {
        "id": 3,
        "title": "你更喜欢哪种天气？",
        "options": [
            {"text": "晴空万里的大晴天", "type": "sunny"},
            {"text": "微风徐徐的阴天", "type": "quiet"},
            {"text": "充满惊喜的雷雨后", "type": "brave"}
        ]
    }
]

# 首页
@app.route('/')
def index():
    return render_template('index.html', questions=questions)

# 结果页
@app.route('/result', methods=['POST'])
def result():
    type_count = {"sunny": 0, "quiet": 0, "brave": 0}
    for q_id in range(1, 4):
        user_choice = request.form.get(f'q{q_id}')
        type_count[user_choice] += 1

    final_type = max(type_count, key=type_count.get)
    return render_template('result.html', result=duck_personality[final_type])

if __name__ == '__main__':
    print("🐥 小黄鸭性格测试网站已启动！")
    print("电脑访问：http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)