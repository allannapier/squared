from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def square_image(image):
    # Get the size of the original image
    width, height = image.size
    # Use the smaller dimension to create a square
    crop_size = min(width, height)
    # Calculate coordinates for cropping
    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    # Crop the image to a square
    cropped = image.crop((left, top, right, bottom))
    
    # Get the target size from the request, default to 300
    target_size = request.form.get('pixel_size', 300, type=int)
    # Ensure target size is within reasonable bounds
    target_size = max(50, min(target_size, 2000))
    
    # Resize the image to the target size
    return cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)

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
        # Open the image using PIL
        image = Image.open(file.stream)
        # Square the image
        squared_image = square_image(image)
        
        # Save the result to a bytes buffer
        img_io = io.BytesIO()
        squared_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return str(e), 400
