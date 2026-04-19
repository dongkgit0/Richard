from flask import Flask, render_template, request, redirect, url_for
import os
import time
import re

app = Flask(__name__)

# 文章存放目录
POST_DIR = "posts"
if not os.path.exists(POST_DIR):
    os.makedirs(POST_DIR)


# ===================== 工具函数：清理标题非法字符（解决本次/报错根源）=====================
def safe_filename(title):

    # Windows系统文件名禁止字符全集
    invalid_chars = r'[\\/:*?"<>|]'
    # 非法字符全部替换为下划线
    safe_title = re.sub(invalid_chars, '_', title)
    # 额外去除首尾空白，防止纯空格标题
    safe_title = safe_title.strip()
    return safe_title


# 首页：显示所有文章（分页 + 按创建时间倒序）
@app.route('/')
def index():
    # 每页显示的文章数量
    PER_PAGE = 10
    # 获取当前页码（默认第1页）
    page = request.args.get('page', 1, type=int)

    # 获取所有文章，并按【真实创建时间】倒序排列
    files = []
    for f in os.listdir(POST_DIR):
        if f.endswith(".txt"):
            file_path = os.path.join(POST_DIR, f)
            create_time = os.path.getctime(file_path)
            files.append((create_time, f))

    # 最新的在最上面
    files.sort(reverse=True)
    files = [f for t, f in files]

    # 计算总页数
    total = len(files)
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    # 确保页码在有效范围内
    page = max(1, min(page, total_pages))

    # 计算当前页显示的文件切片范围
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    current_files = files[start:end]

    # 组装当前页的文章数据
    posts = []
    for fname in current_files:
        path = os.path.join(POST_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            title = f.readline().strip()
        posts.append({
            "id": fname[:-4],
            "title": title
        })

    # 传递分页参数到模板
    return render_template(
        "index.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        PER_PAGE=PER_PAGE,
        total=total
    )


# 查看单篇文章详情
@app.route("/post/<post_id>")
def show_post(post_id):
    path = os.path.join(POST_DIR, f"{post_id}.txt")
    if not os.path.exists(path):
        return "文章不存在", 404
    with open(path, "r", encoding="utf-8") as f:
        title = f.readline().strip()
        content = f.read()
    return render_template("post.html", title=title, content=content, post_id=post_id)


# 编辑文章（修改标题自动重命名文件，本次报错核心修复）
@app.route("/edit/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    old_path = os.path.join(POST_DIR, f"{post_id}.txt")
    if not os.path.exists(old_path):
        return "文章不存在", 404

    if request.method == "GET":
        with open(old_path, "r", encoding="utf-8") as f:
            old_title = f.readline().strip()
            old_content = f.read()
        return render_template("edit.html", post_id=post_id, title=old_title, content=old_content)

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_content = request.form.get("content", "")
        # 仅标题必填，**文章内容完全取消必填校验**（空内容也可以保存）
        if not new_title:
            return "标题不能为空！"

        # ========== 核心修复1：标题转安全文件名，过滤所有非法斜杠/特殊字符 ==========
        safe_new_title = safe_filename(new_title)
        new_path = os.path.join(POST_DIR, f"{safe_new_title}.txt")

        # 只有标题真正发生变化时，才执行改名操作
        if post_id != safe_new_title:
            # 修复：新标题文件已存在的冲突判断
            if os.path.exists(new_path):
                return "该标题已存在，请更换标题！"
            # 此时路径完全合法，不会再报找不到路径错误
            os.rename(old_path, new_path)

        # 写入文件（空内容也正常写入，兼容无内容文章）
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(new_title + "\n")
            f.write(new_content)

        return redirect(url_for("show_post", post_id=safe_new_title))


# 删除文章接口
@app.route("/delete/<post_id>", methods=["POST"])
def delete_post(post_id):
    path = os.path.join(POST_DIR, f"{post_id}.txt")
    if not os.path.exists(path):
        return "文章不存在", 404
    os.remove(path)
    return redirect(url_for("index"))


# 发布新文章（同步修复：安全文件名+内容非必填）
@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "")
        # 只校验标题必填，内容完全放开，空内容可正常发布
        if not title:
            return "标题不能为空！"

        # 同步新建文章也做非法字符过滤，从源头避免问题
        safe_title = safe_filename(title)
        filename = f"{safe_title}.txt"
        path = os.path.join(POST_DIR, filename)

        # 防止重复标题
        if os.path.exists(path):
            return "该标题已存在，请更换标题！"

        with open(path, "w", encoding="utf-8") as f:
            f.write(title + "\n")
            f.write(content)
        return redirect(url_for("index"))
    return render_template("new.html")


if __name__ == "__main__":
    app.run(debug=True, port=8000)