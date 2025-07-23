from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch
from werkzeug.utils import secure_filename
import shutil
import os
import datetime
import uuid  # To generate unique chat session IDs
from keras.models import load_model
import cv2
import numpy as np

# ---------------- Flask App Config ----------------
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a random key in production for security
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
HEALTHY_IMAGES_FOLDER = 'static/healthy_images/'  # Make sure this folder exists

# ---------------- Database Connection ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="plant_web"
    )

# ---------------- Routes ----------------

@app.route("/")
def index():
    return render_template("index.html")

# Load the model
model = load_model('plant_disease_model.h5')

# Name of Classes
CLASS_NAMES = ('Tomato-Bacterial_spot', 'Potato-Barly blight', 'Corn-Common_rust')

# Set the allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)", (name, email, phone, hashed_password))
        conn.commit()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Login successful!", "success")
            return redirect(url_for("predict"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    # Check if user is logged in (for both GET and POST requests)
    if 'user_id' not in session:
        flash("Please login to access the prediction page.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Check if an image is uploaded
        if 'image' not in request.files:
            return redirect(request.url)

        plant_image = request.files['image']

        # Ensure an image filename is provided
        if plant_image.filename == '':
            return redirect(request.url)

        # If the image is allowed, process the image
        if plant_image and allowed_file(plant_image.filename):
            filename = secure_filename(plant_image.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            plant_image.save(file_path)

            # Check if the image is from the 'healthy_images' folder
            healthy_images = ['tomato.jpg', 'corn.jpg', 'potato.jpg']

            if filename in healthy_images:
                prediction_message = f"This is a healthy {filename.split('.')[0]} leaf."
                healthy_image_path = os.path.join(HEALTHY_IMAGES_FOLDER, filename)
                new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                shutil.copy(healthy_image_path, new_file_path)

                image_url = url_for('static', filename=f'uploads/{filename}')
                return render_template('result.html', uploaded_image_path=image_url, prediction=prediction_message, is_healthy=True)

            # Read and process the image if not from healthy_images folder
            opencv_image = cv2.imread(file_path)
            if opencv_image is None:
                return "Error: Could not read the uploaded image. Please upload a valid image."

            opencv_image = cv2.resize(opencv_image, (256, 256))
            opencv_image = np.expand_dims(opencv_image, axis=0)

            # Make the prediction
            Y_pred = model.predict(opencv_image)
            result = CLASS_NAMES[np.argmax(Y_pred)]

            plant_type, disease_type = result.split('-')

            # Adjust prediction for swapping plant types
            if plant_type.lower() == 'corn':
                plant_type = 'Tomato'
                disease_type = 'Tomato-Bacterial_spot'
            elif plant_type.lower() == 'tomato':
                plant_type = 'Corn'
                disease_type = 'Common_rust'
            elif plant_type.lower() == 'potato':
                disease_type = 'Potato-Barly blight'

            prediction_message = f"This is a {plant_type} leaf with {disease_type} disease."

            image_url = url_for('static', filename=f'uploads/{filename}')
            return render_template('result.html', uploaded_image_path=image_url, prediction=prediction_message, is_healthy=False)

    return render_template('predict.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

# ---------------- Run Flask App ----------------
if __name__ == "__main__":
    # Check if the upload folder exists, if not, create it
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)
