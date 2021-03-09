from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests
import config

API_KEY = config.API_KEY
app = Flask(__name__)
app.secret_key = "movie"
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)
Bootstrap(app)

class EditForms(FlaskForm):
    update_rating = FloatField("Your rating out of 10 e.g. 7.5", validators=[DataRequired(), NumberRange(min=0, max=10, message="Number between 1 to 10")])
    update_review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddForms(FlaskForm):
    add_title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

db.create_all()



@app.route("/")
def home():
    all_movies = db.session.query(Movies).order_by(Movies.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)-i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/find/<int:id>")
def select_movie(id):
    movie_id = id
    details = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US')
    res = details.json()
    new_movie = Movies(
        title=res['title'],
        year=res['release_date'].split('-')[0],
        description=res['overview'],
        review="None",
        img_url=f"https://image.tmdb.org/t/p/w500/{res['poster_path']}?api_key={API_KEY}"
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for("edit_movie", id=new_movie.id))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_form = AddForms()

    if add_form.validate_on_submit():
       title = add_form.add_title.data
       data = requests.get(url=f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={title}')
       related_movies = data.json()['results']
       return render_template('select.html', movies=related_movies)

    return render_template('add.html', form=add_form)


@app.route("/edit", methods=['GET', 'POST'])
def edit_movie():

    edit_form = EditForms()

    movie_id = request.args.get('id')

    movie = Movies.query.filter_by(id=movie_id).first()
    if edit_form.validate_on_submit():
       movie.rating = request.form['update_rating']
       movie.review = request.form['update_review']
       db.session.commit()
       return redirect(url_for('home'))

    return render_template('edit.html', movie=movie, form=edit_form)

@app.route("/delete")
def delete_movie():
    movie_id = request.args.get('d_id')
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))
if __name__ == '__main__':
    app.run(debug=True)
