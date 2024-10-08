"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, People, Vehicle, Movie, Favorite
from werkzeug.security import generate_password_hash, check_password_hash
#from models import Person


app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    current_user_id = request.args.get('user_id')
    if not current_user_id:
        return jsonify({"error": "User ID is required"}), 400

    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    return jsonify([favorite.serialize() for favorite in favorites]), 200

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400
    if not data.get('username') or not data.get('firstname') or not data.get('lastname'):
        return jsonify({"error": "Username, firstname, and lastname are required"}), 400
    hashed_password = generate_password_hash(data.get('password'))
    new_user = User(
        email=data.get('email'),
        password=hashed_password,
        is_active=True,
        username=data.get('username'),
        firstname=data.get('firstname'),
        lastname=data.get('lastname'),
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([planet.serialize() for planet in planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    return jsonify([person.serialize() for person in people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_single_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    current_user_id = request.json.get('user_id')
    if not current_user_id:
        return jsonify({"error": "User ID is required"}), 400

    new_favorite = Favorite(user_id=current_user_id, planet_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify(new_favorite.serialize()), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    current_user_id = request.json.get('user_id')
    if not current_user_id:
        return jsonify({"error": "User ID is required"}), 400

    new_favorite = Favorite(user_id=current_user_id, people_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify(new_favorite.serialize()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    current_user_id = request.json.get('user_id')
    if not current_user_id:
        return jsonify({"error": "User ID is required"}), 400

    favorite = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Favorite planet deleted"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    current_user_id = request.json.get('user_id')
    if not current_user_id:
        return jsonify({"error": "User ID is required"}), 400

    favorite = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    if not favorite:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Favorite person deleted"}), 200

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.password = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify(user.serialize()), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
