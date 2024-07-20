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

# Model
class UserFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    file_id = db.Column(db.String(100), unique=True)

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

    user_file = UserFile(name=name, email=email)
    db.session.add(user_file)
    db.session.commit()

    return jsonify({"message": "User added successfully"}), 201

@app.route('/user/<email>/file/<file_id>', methods=['POST'])
def upload_file(email, file_id):
    file = request.files.get('file')

    if not email or not file:
        return jsonify({"error": "Email and file are required"}), 400

    user_file = UserFile.query.filter_by(email=email).first()

    if not user_file:
        return jsonify({"error": "User not found"}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    file.save(file_path)

    user_file.file_id = file_id
    db.session.commit()

    return jsonify({"message": "File uploaded successfully"}), 201

@app.route('/user/<email>', methods=['GET'])
def get_user_by_email(email):
    user_file = UserFile.query.filter_by(email=email).first()
    if not user_file:
        return jsonify({"error": "User not found"}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_file.file_id) if user_file.file_id else None

    if file_path and os.path.exists(file_path):
        return send_file(file_path, download_name=user_file.file_id, as_attachment=True)
    
    return jsonify({
        "name": user_file.name,
        "email": user_file.email,
        "file_id": user_file.file_id
    }), 200

@app.route('/user', methods=['GET'])
def list_users():
    users = UserFile.query.all()
    user_list = [{"name": user.name, "email": user.email, "file_id": user.file_id} for user in users]
    return jsonify(user_list), 200

@app.route('/user/<email>/file', methods=['GET'])
def list_files_for_user(email):
    user_file = UserFile.query.filter_by(email=email).first()
    if not user_file:
        return jsonify({"error": "User not found"}), 404

    files = [user_file.file_id] if user_file.file_id else []
    return jsonify({"email": email, "files": files}), 200

@app.route('/user/<email>/file/<file_id>', methods=['GET'])
def download_file(email, file_id):
    user_file = UserFile.query.filter_by(email=email, file_id=file_id).first()
    if not user_file:
        return jsonify({"error": "File not found"}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if os.path.exists(file_path):
        return send_file(file_path, download_name=file_id, as_attachment=True)
    
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)