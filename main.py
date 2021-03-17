from forms import CreatePostForm, Registration, Login, Comments, PortfolioForm

import datetime as dt
import smtplib
from functools import wraps
import os

from flask import Flask, render_template, redirect, url_for, request, flash
from flask import abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap(app)

year = dt.datetime.now().year
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

my_email = os.environ.get("MY_EMAIL")
pword = os.environ.get("PWORD")
your_addy = os.environ.get("YOUR_ADDY")

## CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///posts.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## GRAVATAR SETUP
gravatar = Gravatar(app,
                    size=50,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

## LOGIN PERMISSIONS SETUP
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return function(*args, **kwargs)
    return wrapper_function

## CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password =db.Column(db.String(), nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    date_order = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment (db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text(), nullable = False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship("BlogPost", back_populates="comments")


class Portfolio (db.Model):
    __tablename__ = "portfolio"
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.Text(), nullable = False)
    title = db.Column(db.Text(), nullable = False)
    date = db.Column(db.String(250), nullable=False)
    date_order = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.String(), nullable=False)
    port_url = db.Column(db.String(), nullable=False)
    body = db.Column(db.Text, nullable=False)


# db.create_all()

## FUNCTIONS
def date_to_number(date):
    long_month_name = date.split(" ")[0]
    print(long_month_name)
    datetime_object = dt.datetime.strptime(long_month_name, "%B")
    month = datetime_object.month
    if int(month)<10:
        month = str(0) + str(month)
    month = str(0) + str(month)
    day = date.split(" ")[1].strip(",")
    if int(day)<10:
        day=str(0)+str(day)
    year = date.split(",")[1].strip(" ")
    date_code = int(str(year) + str(month) + str(day))
    return date_code

## ROUTES

@app.route('/')
def home():
    blog_data = BlogPost.query.order_by(BlogPost.date_order.desc()).all()
    db.session.commit()
    return render_template("index.html", blogs=blog_data, year=year, logged_in=current_user.is_authenticated)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = Registration()
    if form.validate_on_submit():
        if User.query.filter_by(email=request.form['email']).first():
            flash("The email address you have provided already exists in the Communique database. Please login.")
            return redirect(url_for('login'))
        else:
            new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=8)
        )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form=Login()
    if request.method == 'POST':
        password = request.form["password"]
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            flash ("That email does not exist, please try again.")
            return redirect (url_for ('login'))
        elif not check_password_hash(user.password, password):
            flash ("Password not correct, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/all_posts')
def all_posts():
    blog_data = BlogPost.query.order_by(BlogPost.date_order.desc()).all()
    return render_template("all_posts.html", blogs=blog_data, year=year, logged_in=current_user.is_authenticated)


@app.route('/admin')
@admin_only
def admin():
    blog_data = BlogPost.query.order_by(BlogPost.date_order.desc()).all()
    user_data = User.query.order_by(User.id).all()
    comment_data = Comment.query.all()
    port_data = Portfolio.query.all()
    return render_template("admin.html", portfolio = port_data, comments = comment_data, blogs=blog_data, users = user_data, year=year, logged_in=current_user.is_authenticated)


@app.route('/add_port', methods=['GET', 'POST'])
@admin_only
def add_port():
    date = dt.datetime.now().strftime("%B %d, %Y")
    form = PortfolioForm(date=date)
    if form.validate_on_submit():
        new_port = Portfolio(
            topic=form.topic.data,
            title=form.title.data,
            date=form.date.data,
            date_order=date_to_number(form.date.data),
            img_url=form.img_url.data,
            port_url=form.port_url.data,
            body=form.body.data,
        )
        db.session.add(new_port)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add_port.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/new_post', methods=['GET', 'POST'])
@admin_only
def new_post():
    date = dt.datetime.now().strftime("%B %d, %Y")
    form = CreatePostForm(date=date)
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=form.date.data,
            date_order=date_to_number(form.date.data),
            body=form.body.data,
            author_id=current_user.id,
            img_url=form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/edit_post/<int:num>', methods=['GET', 'POST'])
@admin_only
def edit_post(num):
    blog = db.session.query(BlogPost).filter_by(id=num).first()
    edit_form = CreatePostForm(
        title=blog.title,
        subtitle=blog.subtitle,
        date=blog.date,
        img_url=blog.img_url,
        author_id=current_user.id,
        body=blog.body
    )
    if edit_form.validate_on_submit():
        blog.title = edit_form.title.data
        blog.subtitle = edit_form.subtitle.data
        blog.date = edit_form.date.data
        blog.date_order = date_to_number(edit_form.date.data)
        blog.body = edit_form.body.data
        # blog.author_id = current_user.id,
        blog.img_url = edit_form.img_url.data
        db.session.commit()
        print(f"complete{blog.date_order}")
        return redirect(url_for('post', num=num))
    return render_template("edit_post.html", form=edit_form, is_edit=True, num=num, logged_in=current_user.is_authenticated)


@app.route('/edit_port/<int:num>', methods=['GET', 'POST'])
@admin_only
def edit_port(num):
    entry = db.session.query(Portfolio).filter_by(id=num).first()
    edit_form = PortfolioForm(
        topic = entry.topic,
        title=entry.title,
        date=entry.date,
        img_url=entry.img_url,
        port_url=entry.port_url,
        body=entry.body
    )
    if edit_form.validate_on_submit():
        entry.topic = edit_form.topic.data
        entry.title = edit_form.title.data
        entry.date = edit_form.date.data
        entry.date_order = date_to_number(edit_form.date.data)
        entry.img_url = edit_form.img_url.data
        entry.post_url= edit_form.port_url.data
        entry.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template("edit_port.html", form=edit_form, is_edit=True, num=num, logged_in=current_user.is_authenticated)


@app.route('/post/<int:num>', methods=['GET', 'POST'])
def post(num):
    blog_data = db.session.query(BlogPost).filter_by(id=num).first()
    form = Comments()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text = form.text.data,
            author_id = current_user.id,
            comment_author = current_user,
            parent_post = db.session.query(BlogPost).filter_by(id=num).first(),
            post_id = num
        )
        db.session.add(new_comment)
        db.session.commit()
        form.text.data = ""
        return redirect(url_for('post', num=num))
    return render_template("post.html", form = form, blog=blog_data, num=num, year=year, logged_in=current_user.is_authenticated)


@app.route('/delete_post/<int:num>', methods=['GET', 'POST'])
@admin_only
def delete_post(num):
    blog = db.session.query(BlogPost).filter_by(id=num).first()
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete_port/<int:num>', methods=['GET', 'POST'])
@admin_only
def delete_port(num):
    entry = db.session.query(Portfolio).filter_by(id=num).first()
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/delete_user/<int:num>', methods=['GET', 'POST'])
@admin_only
def delete_user(num):
    user = db.session.query(User).filter_by(id=num).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/delete_comment/<int:num>', methods=['GET', 'POST'])
@admin_only
def delete_comment(num):
    comment = db.session.query(Comment).filter_by(id=num).first()
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/about')
def about():
    return render_template("about.html", year=year, logged_in=current_user.is_authenticated)


@app.route('/portfolio')
def portfolio():
    port_data = db.session.query(Portfolio).all()
    return render_template("portfolio.html", portfolio = port_data, year=year, logged_in=current_user.is_authenticated)


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == 'GET':
        return render_template("contact.html", year=year, logged_in=current_user.is_authenticated)
    elif request.method == 'POST':
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]
        print(f"{name}, {email}, {message}")

        connection = smtplib.SMTP("smtp.gmail.com", 587)
        connection.starttls()
        connection.login(user=my_email, password=pword)
        connection.sendmail(from_addr=my_email,
                            to_addrs=your_addy,
                            msg="Subject: Someone got in touch!!\n\n"
                                f"{name} at {email} says:\n\n"
                                f"{message}")
        connection.close()
        return render_template("sent.html")

## RUN APP

if __name__ == "__main__":
    app.run(debug=True)
