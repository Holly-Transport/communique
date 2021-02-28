from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
import datetime as dt
import smtplib

app = Flask(__name__)

year = dt.datetime.now().year
app.config['SECRET_KEY'] = '123'
ckeditor = CKEditor(app)
Bootstrap(app)
my_email = "trbreunion@gmail.com"
password = "ilovedata!"
your_addy = "hkrambeck@gmail.com"
your_name = "Jane Jet"

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


@app.route('/')
def home():
    blog_data = BlogPost.query.order_by(BlogPost.date_order.desc()).all()
    db.session.commit()
    return render_template("index.html", blogs=blog_data, year=year)


@app.route('/all_posts')
def all_posts():
    blog_data = BlogPost.query.order_by(BlogPost.date_order.desc()).all()
    return render_template("all_posts.html", blogs=blog_data, year=year)


@app.route('/post/<int:num>')
def post(num):
    blog_data = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template("post.html", blogs=blog_data, num=num, year=year)


@app.route('/new_post', methods=['GET', 'POST'])
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
    return render_template("make-post.html", form=form)


@app.route('/edit_post/<int:num>', methods=['GET', 'POST'])
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
    return render_template("edit_post.html", form=edit_form, is_edit=True, num=num)

@app.route('/delete_post/<int:num>', methods=['GET', 'POST'])
def delete_post(num):
    blog = db.session.query(BlogPost).filter_by(id=num).first()
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template("about.html", year=year)


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == 'GET':
        return render_template("contact.html", year=year)
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
