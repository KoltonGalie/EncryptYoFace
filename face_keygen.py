import cv2
import mediapipe as mp
import numpy as np
import hashlib
import base64

from cryptography.hazmat.primitives.ciphers import Cipher

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

SELECTED_LANDMARKS = list(range(33, 134)) + list(range(1, 21)) + list(range(61, 89))

# Parameters
THRESHOLD = 0.65  # small value to ignore minor variations
BIN_SIZE = 0.05  # size for binning

# list to store all generated keys
generated_keys = []


# Normalizing face landmarks
def normalize_landmarks(landmarks):
    landmarks = np.array([[pt.x, pt.y, pt.z] for pt in landmarks])
    center = landmarks[62]  # nose tip
    normalized = landmarks - center
    max_distance = np.max(np.linalg.norm(normalized, axis=1))
    if max_distance > 0:
        normalized /= max_distance
    return normalized


# Capture face vector from an image
def capture_face_vector(image):
    rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb_frame)

    face_vector = None
    if result.multi_face_landmarks:
        landmarks = result.multi_face_landmarks[0].landmark
        normalized_landmarks = normalize_landmarks(landmarks)
        face_vector = normalized_landmarks.flatten()

    if face_vector is None:
        raise Exception("No face landmarks detected.")

    return face_vector


# Generate key from face vector with smoothing
def generate_key_from_face(face_vector: np.ndarray) -> bytes:
    # apply the binning and rounding to eliminate small variations
    face_vector = np.round(face_vector, 2)
    binned = np.round(face_vector / BIN_SIZE) * BIN_SIZE
    binned = np.round(binned, 2)

    # Apply thresholding to ignore small variations
    for i in range(len(binned) - 1):
        if abs(binned[i] - binned[i + 1]) < THRESHOLD:
            binned[i + 1] = binned[i]

    stable_part = binned[:30]  # use only the first 30 stable values
    normalized = np.clip((stable_part * 50).astype(np.int8), -128, 127)

    # hash the fixed-size byte array
    byte_buffer = normalized.tobytes()

    # generate SHA-256 hash for the encryption key
    digest = hashlib.sha256(byte_buffer).digest()
    return base64.urlsafe_b64encode(digest)





# Example usage
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)

    cap.release()
    cv2.destroyAllWindows()
