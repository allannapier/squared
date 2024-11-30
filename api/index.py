from flask import Flask, render_template, request, send_file
import cv2
import numpy as np
import io
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def square_image(file_stream):
    # Read image file stream into numpy array
    file_bytes = np.frombuffer(file_stream.read(), np.uint8)
    # Read image in RGB mode directly
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    # Convert BGR to RGB right after reading
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Get the size of the original image
    height, width = image.shape[:2]
    
    # Use the smaller dimension to create a square
    crop_size = min(width, height)
    
    # Calculate coordinates for cropping
    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    
    # Crop the image to a square
    cropped = image[top:top+crop_size, left:left+crop_size]
    
    # Get the target size from the request, default to 300
    target_size = request.form.get('pixel_size', 300, type=int)
    # Ensure target size is within reasonable bounds
    target_size = max(50, min(target_size, 2000))
    
    # Resize the image to the target size
    resized = cv2.resize(cropped, (target_size, target_size), interpolation=cv2.INTER_LANCZOS4)
    
    # Convert back to BGR for imencode
    resized = cv2.cvtColor(resized, cv2.COLOR_RGB2BGR)
    
    # Encode the image to PNG
    _, buffer = cv2.imencode('.png', resized)
    return io.BytesIO(buffer.tobytes())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    try:
        # Process the image
        img_io = square_image(file)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return str(e), 400
