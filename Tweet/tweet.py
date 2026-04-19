from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 生产环境请修改
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///x_clone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ------------------------------
# 数据库模型（用户、推文、关注、点赞）
# ------------------------------

# 用户关注多对多关系表
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # 关系
    tweets = db.relationship('Tweet', backref='author', lazy=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_tweets(self):
        # 时间线：自己 + 关注的人的推文
        followed = Tweet.query.join(
            followers, (followers.c.followed_id == Tweet.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Tweet.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Tweet.timestamp.desc())


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)  # X 限制 280 字符
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='tweet', lazy='dynamic')
    comments = db.relationship('Comment', backref='tweet', lazy=True)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    user = db.relationship('User', backref='likes')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(150), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    user = db.relationship('User', backref='comments')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------------
# 路由（页面 + 功能）
# ------------------------------

@app.route('/')
@login_required
def index():
    # 主页 = 时间线
    tweets = current_user.followed_tweets()
    return render_template('index.html', tweets=tweets)


@app.route('/explore')
def explore():
    # 发现页：所有最新推文
    tweets = Tweet.query.order_by(Tweet.timestamp.desc()).all()
    return render_template('index.html', tweets=tweets)


@app.route('/post_tweet', methods=['POST'])
@login_required
def post_tweet():
    content = request.form.get('content')
    if content and len(content) <= 280:
        tweet = Tweet(content=content, author=current_user)
        db.session.add(tweet)
        db.session.commit()
        flash('推文发布成功！')
    return redirect(url_for('index'))


@app.route('/like/<int:tweet_id>')
@login_required
def like(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    like = Like.query.filter_by(user=current_user, tweet=tweet).first()
    if like:
        db.session.delete(like)
    else:
        new_like = Like(user=current_user, tweet=tweet)
        db.session.add(new_like)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/comment/<int:tweet_id>', methods=['POST'])
@login_required
def comment(tweet_id):
    content = request.form.get('content')
    if content:
        comment = Comment(content=content, user=current_user, tweet_id=tweet_id)
        db.session.add(comment)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('不能关注自己')
        return redirect(request.referrer)
    current_user.follow(user)
    db.session.commit()
    flash(f'成功关注 {user.username}')
    return redirect(request.referrer)


@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    current_user.unfollow(user)
    db.session.commit()
    flash(f'已取消关注 {user.username}')
    return redirect(request.referrer)


@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    tweets = Tweet.query.filter_by(author=user).order_by(Tweet.timestamp.desc()).all()
    return render_template('profile.html', user=user, tweets=tweets)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('用户名或密码错误')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('邮箱已注册')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # 新增这一行代码：退出登录时 彻底清空所有flash消息缓存
    session.clear()
    return redirect(url_for('login'))


# 创建数据库
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=4000)