from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

# Create uploads folder if not exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)

class UserFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), db.ForeignKey('user.email'), nullable=False)
    file_id = db.Column(db.String(100))

# Ensure the database tables are created within the application context
with app.app_context():
    db.create_all()

@app.route('/user', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User added successfully"}), 201

@app.route('/user/<email>/file', methods=['POST'])
def upload_file(email):
    file = request.files.get('file')

    if not email or not file:
        return jsonify({"error": "Email and file are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    file_id = f"{email}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    file.save(file_path)

    user_file = UserFile(email=email, file_id=file_id)
    db.session.add(user_file)
    db.session.commit()

    return jsonify({"message": "File uploaded successfully"}), 201

@app.route('/user/<email>', methods=['GET'])
def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_files = UserFile.query.filter_by(email=email).all()
    file_ids = [user_file.file_id for user_file in user_files]

    return jsonify({
        "name": user.name,
        "email": user.email,
        "file_ids": file_ids
    }), 200

@app.route('/user', methods=['GET'])
def list_users():
    users = User.query.all()
    user_list = []
    for user in users:
        user_files = UserFile.query.filter_by(email=user.email).all()
        file_ids = [user_file.file_id for user_file in user_files]
        user_list.append({"name": user.name, "email": user.email, "file_ids": file_ids})
    return jsonify(user_list), 200

@app.route('/user/<email>/file', methods=['GET'])
def list_files_for_user(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_files = UserFile.query.filter_by(email=email).all()
    file_ids = [user_file.file_id for user_file in user_files]

    return jsonify({"email": email, "file_ids": file_ids}), 200

#@app.route('/user/<email>/file/<file_id>', methods=['GET'])
#def download_file(email, file_id):
#    user_file = UserFile.query.filter_by(email=email, file_id=file_id).first()
#    if not user_file:
#        return jsonify({"error": "File not found"}), 404
#
#    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
#    if os.path.exists(file_path):
#        return send_file(file_path, download_name=file_id, as_attachment=True)
#    
#    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)