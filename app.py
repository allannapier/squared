from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def square_image(image):
    # Get the size of the original image
    width, height = image.size
    # Use the smaller dimension to create a square
    size = min(width, height)
    # Calculate coordinates for cropping
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size
    # Crop the image to a square
    return image.crop((left, top, right, bottom))

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

if __name__ == '__main__':
    app.run(debug=True)# Initialize a new Poetry project