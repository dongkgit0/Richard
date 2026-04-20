from flask import Flask, render_template, request, redirect, url_for
import os
import re

app = Flask(__name__)

POST_DIR = "posts"
if not os.path.exists(POST_DIR):
    os.makedirs(POST_DIR)


def safe_filename(title):
    invalid_chars = r'[\\/:*?"<>|]'
    safe_title = re.sub(invalid_chars, '_', title)
    safe_title = safe_title.strip()
    return safe_title


@app.route('/')
def index():
    # 完整分页全部变量，解决首页total未定义报错
    PER_PAGE = 10
    page = request.args.get('page', 1, type=int)

    files = []
    for f in os.listdir(POST_DIR):
        if f.endswith(".txt"):
            file_path = os.path.join(POST_DIR, f)
            create_time = os.path.getctime(file_path)
            files.append((create_time, f))

    files.sort(reverse=True)
    files = [f for t, f in files]

    total = len(files)
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    page = max(1, min(page, total_pages))

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    current_files = files[start:end]

    posts = []
    for fname in current_files:
        path = os.path.join(POST_DIR, fname)
        with open(path, "r", encoding="utf-8") as file:
            title = file.readline().rstrip('\n')
        posts.append({
            "id": fname[:-4],
            "title": title
        })

    # 所有模板变量完整传递，彻底解决Jinja2报错
    return render_template(
        "index.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        PER_PAGE=PER_PAGE,
        total=total
    )


@app.route("/post/<post_id>")
def show_post(post_id):
    path = os.path.join(POST_DIR, f"{post_id}.txt")
    if not os.path.exists(path):
        return "文章不存在", 404
    with open(path, "r", encoding="utf-8") as file:
        all_file = file.read()
    # 严格分割：标题独立一行，正文完整原封不动读取
    first_newline_pos = all_file.find('\n')
    title = all_file[:first_newline_pos]
    content = all_file[first_newline_pos + 1:]
    return render_template("post.html", title=title, content=content, post_id=post_id)


@app.route("/edit/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    old_path = os.path.join(POST_DIR, f"{post_id}.txt")
    if not os.path.exists(old_path):
        return "文章不存在", 404

    if request.method == "GET":
        with open(old_path, "r", encoding="utf-8") as file:
            all_file = file.read()
        first_newline_pos = all_file.find('\n')
        old_title = all_file[:first_newline_pos]
        old_content = all_file[first_newline_pos + 1:]
        return render_template("edit.html", post_id=post_id, title=old_title, content=old_content)

    if request.method == "POST":
        new_title = request.form.get("title", "")
        new_content = request.form.get("content", "")
        if not new_title.strip():
            return "标题不能为空！"

        safe_new_title = safe_filename(new_title)
        new_path = os.path.join(POST_DIR, f"{safe_new_title}.txt")

        if post_id != safe_new_title:
            if os.path.exists(new_path):
                return "该标题已存在，请更换标题！"
            os.rename(old_path, new_path)

        # 缩进完全正确 + 写入逻辑正确：仅1个换行分隔标题正文，不多空行
        with open(new_path, "w", encoding="utf-8") as file:
            file.write(new_title + '\n' + new_content)

        return redirect(url_for("show_post", post_id=safe_new_title))


@app.route("/delete/<post_id>", methods=["POST"])
def delete_post(post_id):
    path = os.path.join(POST_DIR, f"{post_id}.txt")
    if not os.path.exists(path):
        return "文章不存在", 404
    os.remove(path)
    return redirect(url_for("index"))


@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        if not title.strip():
            return "标题不能为空！"

        safe_title = safe_filename(title)
        filename = f"{safe_title}.txt"
        path = os.path.join(POST_DIR, filename)

        if os.path.exists(path):
            return "该标题已存在，请更换标题！"

        # 缩进全部修正，语法100%标准，无任何爆红
        with open(path, "w", encoding="utf-8") as file:
            file.write(title + '\n' + content)
        return redirect(url_for("index"))
    return render_template("new.html")


if __name__ == "__main__":
    app.run(debug=True, port=8000)