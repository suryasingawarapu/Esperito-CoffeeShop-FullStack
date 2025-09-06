import logging
from flask import Flask, request, jsonify, send_file
from flask_pymongo import PyMongo
import bcrypt
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# MongoDB connection URI (make sure to use your MongoDB URI here)
app.config["MONGO_URI"] = "mongodb://localhost:27017/espresso"
mongo = PyMongo(app)

# Check MongoDB connection and database name at startup
try:
    mongo.cx.server_info()  # Force connection
    db_names = mongo.cx.list_database_names()
    if "espresso" in db_names:
        print("Connected to MongoDB. Using database: 'espresso'")
    else:
        print("Database 'espresso' does not exist. It will be created upon the first insert operation.")
except Exception as e:
    print("Failed to connect to MongoDB:", e)

# MongoDB collections
users_collection = mongo.db.users
reservations_collection = mongo.db.reservations  # New collection for reservations

# Route to serve index.html from the project root
@app.route('/')
def home():
    return send_file("index.html")

# Route to serve loginform.html from the project root
@app.route('/loginform.html')
def login_form():
    return send_file("loginform.html")

# Route to serve reservations.html from the project root
@app.route('/reservations.html')
def reservations():
    return send_file("reservations.html")

@app.route('/signup-form', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        print("Received signup form data:", data)
        app.logger.debug(f"Received signup data: {data}")

        if not data.get('username') or not data.get('password') or not data.get('fullname'):
            print("Validation failed: missing required fields")
            return jsonify({'success': False, 'message': 'Please provide all required fields'}), 400

        existing_user = users_collection.find_one({'username': data['username']})
        if existing_user:
            print("User already exists:", data['username'])
            return jsonify({'success': False, 'message': 'Username already exists!'}), 400

        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        user = {
            'fullname': data['fullname'],
            'username': data['username'],
            'email': data.get('email'),
            'password': hashed_password,
            'gender': data.get('gender')
        }

        users_collection.insert_one(user)
        print("User inserted into the database:", user)
        return jsonify({'success': True, 'message': 'User created successfully!'}), 200

    except Exception as e:
        print("Error during signup:", e)
        traceback.print_exc()  # Prints full error traceback to terminal
        app.logger.error(f"Error during signup: {str(e)}")
        return jsonify({'success': False, 'message': f"Error occurred during signup: {str(e)}"}), 500

@app.route('/login-form', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("Received login form data:", data)

        user = users_collection.find_one({'username': data['username']})
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            print("Login successful for user:", data['username'])
            return jsonify({'success': True, 'message': 'Login successful!'}), 200
        else:
            print("Invalid login credentials for user:", data.get('username'))
            return jsonify({'success': False, 'message': 'Invalid credentials!'}), 400

    except Exception as e:
        print("Error during login:", e)
        traceback.print_exc()
        app.logger.error(f"Error during login: {str(e)}")
        return jsonify({'success': False, 'message': f"Error occurred during login: {str(e)}"}), 500

# New endpoint to handle reservation submissions
@app.route('/submit_reservation', methods=['POST'])
def submit_reservation():
    try:
        data = request.get_json()
        print("Received reservation data:", data)
        app.logger.debug(f"Reservation data: {data}")

        # Validate required fields
        required_fields = ['name', 'email', 'date', 'time', 'guests', 'occasion']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            message = f"Missing required fields: {', '.join(missing_fields)}"
            print(message)
            return jsonify({'success': False, 'message': message}), 400

        # Insert reservation data into the database
        reservations_collection.insert_one(data)
        print("Reservation saved:", data)
        return jsonify({'success': True, 'message': 'Reservation created successfully!'}), 200

    except Exception as e:
        print("Error during reservation:", e)
        traceback.print_exc()
        app.logger.error(f"Error during reservation: {str(e)}")
        return jsonify({'success': False, 'message': f"Error occurred during reservation: {str(e)}"}), 500

# Optional: Endpoint to retrieve all reservations (for UI display purposes)
@app.route('/get_reservations', methods=['GET'])
def get_reservations():
    try:
        reservations = list(reservations_collection.find({}))
        # Convert MongoDB ObjectId to string for JSON serialization
        for reservation in reservations:
            reservation['_id'] = str(reservation['_id'])
        return jsonify({'success': True, 'reservations': reservations}), 200
    except Exception as e:
        print("Error fetching reservations:", e)
        traceback.print_exc()
        app.logger.error(f"Error fetching reservations: {str(e)}")
        return jsonify({'success': False, 'message': f"Error occurred while fetching reservations: {str(e)}"}), 500

if __name__ == '__main__':
    # Running on port 5002 to match the fetch URL in your reservations.html
    app.run(debug=True, port=5002)
