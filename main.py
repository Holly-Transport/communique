from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
import datetime as dt
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from flask import abort
import os
# from forms import CreatePostForm
# from flask_gravatar import Gravatar


app = Flask(__name__)

year = dt.datetime.now().year
app.config['SECRET_KEY'] = '123'
ckeditor = CKEditor(app)
Bootstrap(app)
my_email = MY_EMAIL
password = PASSWORD
your_addy = YOUR_ADDY
your_name = YOUR_NAME

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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


##CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    date_order = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password =db.Column(db.String(), nullable=False)

# db.create_all()

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    date = StringField("Date (Month DD, YYYY)")
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class Registration(FlaskForm):
    name = StringField("First Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password =PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class Login(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

##Functions
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

##Routes

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


@app.route('/post/<int:num>')
def post(num):
    blog_data = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template("post.html", blogs=blog_data, num=num, year=year, logged_in=current_user.is_authenticated)


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
            author=form.author.data,
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
        author=blog.author,
        body=blog.body
    )
    if edit_form.validate_on_submit():
        blog.title = edit_form.title.data
        blog.subtitle = edit_form.subtitle.data
        blog.date = edit_form.date.data
        blog.date_order = date_to_number(edit_form.date.data)
        blog.body = edit_form.body.data
        blog.author = edit_form.author.data
        blog.img_url = edit_form.img_url.data
        db.session.commit()
        print(f"complete{blog.date_order}")
        return redirect(url_for('post', num=num))
    return render_template("edit_post.html", form=edit_form, is_edit=True, num=num, logged_in=current_user.is_authenticated)

@app.route('/delete_post/<int:num>', methods=['GET', 'POST'])
def delete_post(num):
    blog = db.session.query(BlogPost).filter_by(id=num).first()
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template("about.html", year=year, logged_in=current_user.is_authenticated)

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
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email,
                            to_addrs=your_addy,
                            msg="Subject: Someone got in touch!!\n\n"
                                f"{name} at {email} says:\n\n"
                                f"{message}")
        connection.close()
        return render_template("sent.html")


if __name__ == "__main__":
    app.run(debug=True)
