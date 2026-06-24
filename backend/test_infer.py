import base64
import json
import cv2
import numpy as np
import requests

# Create a dummy white image frame
dummy_img = np.ones((224, 224, 3), dtype=np.uint8) * 255
_, buffer = cv2.imencode('.jpg', dummy_img)
jpg_as_text = base64.b64encode(buffer).decode('utf-8')

url = "http://127.0.0.1:8000/infer"
payload = {"frame": jpg_as_text}

print("Sending dummy frame to Falcon API...")
try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to API. Is uvicorn running?")