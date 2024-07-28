from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Define the base directory
base_directory = os.path.abspath(os.path.dirname(__file__))

# Define the data directory and ensure it exists
data_directory = os.path.join(base_directory, 'data')
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

# Configure the instance path and ensure it exists
instance_directory = os.path.join(data_directory, 'instance')
if not os.path.exists(instance_directory):
    os.makedirs(instance_directory)

# Configure the database and upload paths
db_path = os.path.join(instance_directory, 'data.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['UPLOAD_FOLDER'] = os.path.join(data_directory, 'uploads')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Print paths for debugging
print(f"Base Directory: {base_directory}")
print(f"Data Directory: {data_directory}")
print(f"Instance Directory: {instance_directory}")
print(f"Database Path: {db_path}")
print(f"Upload Folder: {app.config['UPLOAD_FOLDER']}")

db = SQLAlchemy(app)

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
    try:
        db.create_all()
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

@app.route('/user', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": "User already exists"}), 409
    else:
        new_user = User(name=name, email=email)
        db.session.add(new_user)
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

@app.route('/user/<email>', methods=['DELETE'])
def delete_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Delete associated files
    user_files = UserFile.query.filter_by(email=email).all()
    for user_file in user_files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_file.file_id)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(user_file)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"User with email {email} and associated files deleted successfully"}), 200

@app.route('/user', methods=['DELETE'])
def delete_all_users():
    users = User.query.all()
    for user in users:
        user_files = UserFile.query.filter_by(email=user.email).all()
        for user_file in user_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_file.file_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(user_file)

        db.session.delete(user)
    
    db.session.commit()

    return jsonify({"message": "All users and associated files deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)