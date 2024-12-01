import sentry_sdk
from flask import Flask, render_template, request, send_file
import cv2
import numpy as np
import io
import os
import traceback
import sys

# Initialize Sentry
sentry_sdk.init(
    dsn="https://72abe17308dbee6e9186461079178adf@o4506175218253824.ingest.us.sentry.io/4508391974174720",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler when possible.
        "continuous_profiling_auto_start": True,
    },
)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def encode_image(image, format='png'):
    """Encode image to specified format"""
    try:
        if format.lower() == 'png':
            ext = '.png'
            params = []
        elif format.lower() == 'jpeg':
            ext = '.jpg'
            params = [cv2.IMWRITE_JPEG_QUALITY, 95]  # High quality JPEG
        elif format.lower() == 'webp':
            ext = '.webp'
            params = [cv2.IMWRITE_WEBP_QUALITY, 95]  # High quality WebP
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        success, buffer = cv2.imencode(ext, image, params)
        if not success:
            raise ValueError(f"Failed to encode image to {format}")
        return buffer
    except Exception as e:
        print(f"Error encoding image: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def square_image(file_stream):
    try:
        # Read the file into memory
        file_content = file_stream.read()
        if not file_content:
            raise ValueError("Empty file received")
        
        print(f"File content length: {len(file_content)} bytes", file=sys.stderr)

        # Convert to numpy array
        file_bytes = np.frombuffer(file_content, np.uint8)
        if len(file_bytes) == 0:
            raise ValueError("No data in file buffer")
        
        print(f"Numpy array shape: {file_bytes.shape}", file=sys.stderr)

        # Decode the image
        image = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("Failed to decode image")
        
        print(f"Decoded image shape: {image.shape}", file=sys.stderr)

        # If image has an alpha channel, convert to RGB
        if len(image.shape) == 3 and image.shape[2] == 4:
            print("Converting RGBA to RGB", file=sys.stderr)
            # Convert RGBA to RGB
            alpha = image[:, :, 3]
            background = np.full_like(image[:, :, :3], 255)
            image = background * (1 - alpha[:, :, np.newaxis] / 255.0) + \
                   image[:, :, :3] * (alpha[:, :, np.newaxis] / 255.0)
            image = image.astype(np.uint8)
        elif len(image.shape) == 2:
            print("Converting grayscale to RGB", file=sys.stderr)
            # Convert grayscale to RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Convert BGR to RGB
        if len(image.shape) == 3:
            print("Converting BGR to RGB", file=sys.stderr)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get dimensions
        height, width = image.shape[:2]
        print(f"Image dimensions: {width}x{height}", file=sys.stderr)
        
        # Calculate square crop
        crop_size = min(width, height)
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        
        # Perform crop
        cropped = image[top:top+crop_size, left:left+crop_size]
        print(f"Cropped size: {crop_size}x{crop_size}", file=sys.stderr)
        
        # Get target size
        target_size = request.form.get('pixel_size', 300, type=int)
        target_size = max(50, min(target_size, 2000))
        print(f"Target size: {target_size}x{target_size}", file=sys.stderr)
        
        # Resize image
        resized = cv2.resize(cropped, (target_size, target_size), 
                           interpolation=cv2.INTER_LANCZOS4)
        
        # Convert back to BGR for encoding
        resized = cv2.cvtColor(resized, cv2.COLOR_RGB2BGR)
        
        # Get output format
        format = request.form.get('format', 'png')
        print(f"Output format: {format}", file=sys.stderr)
        
        # Encode to specified format
        buffer = encode_image(resized, format)
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
        
        print(f"Processing file: {file.filename}", file=sys.stderr)
        print(f"Content type: {file.content_type}", file=sys.stderr)

        # Process the image
        img_io = square_image(file)
        img_io.seek(0)
        
        # Get the format for the response mimetype
        format = request.form.get('format', 'png')
        mimetype = f'image/{format}'
        
        return send_file(img_io, mimetype=mimetype)
        
    except Exception as e:
        print(f"Error processing image: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return f"Error processing image: {str(e)}", 400
