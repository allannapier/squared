from flask import Flask, render_template, request, send_file
import cv2
import numpy as np
import io
import os
import traceback
import sys

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def square_image(file_stream):
    try:
        # Read the file into memory
        file_content = file_stream.read()
        if not file_content:
            raise ValueError("Empty file received")

        # Convert to numpy array
        file_bytes = np.frombuffer(file_content, np.uint8)
        if len(file_bytes) == 0:
            raise ValueError("No data in file buffer")

        # Decode the image
        image = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("Failed to decode image")

        # If image has an alpha channel, convert to RGB
        if len(image.shape) == 3 and image.shape[2] == 4:
            # Convert RGBA to RGB
            alpha = image[:, :, 3]
            background = np.full_like(image[:, :, :3], 255)
            image = background * (1 - alpha[:, :, np.newaxis] / 255.0) + \
                   image[:, :, :3] * (alpha[:, :, np.newaxis] / 255.0)
            image = image.astype(np.uint8)
        elif len(image.shape) == 2:
            # Convert grayscale to RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Convert BGR to RGB
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get dimensions
        height, width = image.shape[:2]
        
        # Calculate square crop
        crop_size = min(width, height)
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        
        # Perform crop
        cropped = image[top:top+crop_size, left:left+crop_size]
        
        # Get target size
        target_size = request.form.get('pixel_size', 300, type=int)
        target_size = max(50, min(target_size, 2000))
        
        # Resize image
        resized = cv2.resize(cropped, (target_size, target_size), 
                           interpolation=cv2.INTER_LANCZOS4)
        
        # Convert back to BGR for encoding
        resized = cv2.cvtColor(resized, cv2.COLOR_RGB2BGR)
        
        # Encode to PNG
        success, buffer = cv2.imencode('.png', resized)
        if not success:
            raise ValueError("Failed to encode output image")
            
        return io.BytesIO(buffer.tobytes())
        
    except Exception as e:
        print(f"Error in square_image: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        # Process the image
        img_io = square_image(file)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        print(f"Error processing image: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return f"Error processing image: {str(e)}", 400
