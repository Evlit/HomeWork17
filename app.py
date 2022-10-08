# Домашка 17

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False}
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)

# Объявляем модели базы данных


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre = fields.Method('Get_genre')
    director = fields.Method('Get_director')

    def Get_genre(self, text_):
        return text_.genre.name

    def Get_director(self, text_):
        return text_.director.name

# Объявляем схемы и неймспэйсы базы данных


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


session = db.session()
movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)
genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)

api = Api(app)
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')

# Описание вьюшек


@movie_ns.route('/')
class MoviesView(Resource):
    """
    Класс фильмов
    """
    def get(self):
        """
        Обработка запросов Get
        в зависимости от параметров - все или по жанру и/или режиссеру
        """
        key_dir = int(request.args.get('director_id', 0))
        key_genre = int(request.args.get('genre_id', 0))
        if key_dir + key_genre == 0:
            return movies_schema.dump(db.session.query(Movie).all()), 200
        elif key_dir > 0 and key_genre == 0:
            result = db.session.query(Movie).filter(Movie.director_id == key_dir).all()
            if len(result) > 0:
                return movies_schema.dump(result), 200
            else:
                return "В базе нет записей с таким номером"
        elif key_dir == 0 and key_genre > 0:
            result = db.session.query(Movie).filter(Movie.genre_id == key_genre).all()
            if len(result) > 0:
                return movies_schema.dump(result), 200
            else:
                return "В базе нет записей с таким номером"
        elif key_dir > 0 and key_genre > 0:
            result = db.session.query(Movie).filter(Movie.director_id == key_dir, Movie.genre_id == key_genre).all()
            if len(result) > 0:
                return movies_schema.dump(result), 200
            else:
                return "В базе нет записей с таким номером"

    def post(self):
        """
        Обработка POST - добавление фильма
        """
        data = request.json
        new_movie = Movie(**data)
        db.session.add(new_movie)
        db.session.commit()
        return "", 201


@movie_ns.route('/<int:mid>')
class MovieView(Resource):
    """
    Класс фильма по id
    """
    def get(self, mid):
        """
        Вывод фильма по id
        """
        try:
            result = Movie.query.get(mid)
            return movie_schema.dump(result), 200
        except Exception as e:
            return f"Нет записи с таким номером {e}"

    def put(self, mid: int):
        """
        Обработка запроса PUT
        """
        movie = Movie.query.get(mid)
        if not movie:
            return "", 404
        data = request.json
        movie.title = data.get("title")
        movie.description = data.get("description")
        movie.trailer = data.get("trailer")
        movie.year = data.get("year")
        movie.rating = data.get("rating")
        db.session.commit()
        return "", 204

    def delete(self, mid: int):
        """
        Обработка запроса DELETE
        """
        movie = Movie.query.get(mid)
        if not movie:
            return "", 404
        db.session.delete(movie)
        db.session.commit()
        return "", 204


@director_ns.route('/')
class DirectorsView(Resource):
    """
    Класс режиссеров
    """
    def get(self):
        """
        Вывод всех режиссеров для проверки
        результатов запросов PUT, POST, DELETE
        """
        return directors_schema.dump(db.session.query(Director).all()), 200

    def post(self):
        """
        Обработка POST - добавление режиссера
        """
        data = request.json
        new_dir = Director(**data)
        db.session.add(new_dir)
        db.session.commit()
        return "", 201


@director_ns.route('/<int:did>')
class DirectorView(Resource):
    """
    Класс режиссер
    """
    def get(self, did):
        """
        Вывод режиссера по id для проверки
        результатов запросов PUT, POST, DELETE
        """
        director = Director.query.get(did)
        if not director:
            return "", 404
        return director_schema.dump(director)

    def put(self, did: int):
        """
        Обработка запроса PUT
        """
        director = Director.query.get(did)
        if not director:
            return "", 404
        data = request.json
        director.name = data.get("name")
        db.session.commit()
        return "", 204

    def delete(self, did: int):
        """
        Обработка запроса DELETE
        """
        director = Director.query.get(did)
        if not director:
            return "", 404
        db.session.delete(director)
        db.session.commit()
        return "", 204


@genre_ns.route('/')
class GenresView(Resource):
    """
    Класс жанров
    """
    def get(self):
        """
        Вывод всех жанров для проверки
        результатов запросов PUT, POST, DELETE
        """
        return genres_schema.dump(db.session.query(Genre).all()), 200

    def post(self):
        """
        Обработка запроса POST
        """
        data = request.json
        new_genre = Genre(**data)
        db.session.add(new_genre)
        db.session.commit()
        return "", 201


@genre_ns.route('/<int:gid>')
class GenreView(Resource):
    """
    Класс жанра
    """
    def get(self, gid):
        """
        Вывод жанра по id для проверки
        результатов запросов PUT, POST, DELETE
        """
        genre = Genre.query.get(gid)
        if not genre:
            return "", 404
        return genre_schema.dump(genre)

    def put(self, gid: int):
        """
        Обработка запроса PUT
        """
        genre = Genre.query.get(gid)
        if not genre:
            return "", 404
        data = request.json
        genre.name = data.get("name")
        db.session.commit()
        return "", 204

    def delete(self, gid: int):
        """
        Обработка запроса DELETE
        """
        genre = Genre.query.get(gid)
        if not genre:
            return "", 404
        db.session.delete(genre)
        db.session.commit()
        return "", 204


if __name__ == '__main__':
    app.run(debug=True)
