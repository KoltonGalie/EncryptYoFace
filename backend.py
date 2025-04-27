from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
from face_keygen import capture_face_vector, generate_key_from_face
from crypto_util import encrypt_message, decrypt_message
import cv2
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/capture-face', methods=['POST'])
def capture_face():
    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({'error': 'No image data received'}), 400

        image_data = image_data.split(',')[1]
        img_bytes = base64.b64decode(image_data)
        img = Image.open(BytesIO(img_bytes))

        img = np.array(img)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        face_vector = capture_face_vector(img_rgb)

        if face_vector is None:
            return jsonify({'error': 'No face detected'}), 400

        key = generate_key_from_face(face_vector)

        # Ensure the key is URL-safe base64 encoded (32 bytes)
        key_base64 = base64.urlsafe_b64encode(key).decode()

        return jsonify({'face_vector': face_vector.tolist(), 'key': key_base64})

    except Exception as e:
        print(f"Error in /capture-face: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500

@app.route('/encrypt', methods=['POST'])
def encrypt():
    try:
        data = request.get_json()
        text = data.get('text')
        key = data.get('key')

        if not text or not key:
            return jsonify({'error': 'Text or key not provided'}), 400

        # Convert key from base64 to bytes if needed
        key_bytes = base64.urlsafe_b64decode(key)

        encrypted_text = encrypt_message(text, key_bytes)
        return jsonify({'encrypted_text': encrypted_text.decode()})  # Ensure it's decoded to a string

    except Exception as e:
        print(f"Error in /encrypt: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500

@app.route('/decrypt', methods=['POST'])
def decrypt():
    try:
        data = request.get_json()
        encrypted_text = data.get('encrypted_text')
        key = data.get('key')

        if not encrypted_text or not key:
            return jsonify({'error': 'Encrypted text or key not provided'}), 400

        # Convert key from base64 to bytes if needed
        key_bytes = base64.urlsafe_b64decode(key)

        decrypted_text = decrypt_message(encrypted_text.encode(), key_bytes)  # Encrypt first as bytes
        return jsonify({'decrypted_text': decrypted_text})

    except Exception as e:
        print(f"Error in /decrypt: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
