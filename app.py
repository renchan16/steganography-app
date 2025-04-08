from flask import Flask, render_template, request, send_file, url_for
from PIL import Image
import os

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DELIMITER = "#####"

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

def encode_image(image_path, message):
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    encoded = img.copy()
    binary_msg = text_to_binary(message + DELIMITER)
    data_index = 0
    pixels = list(encoded.getdata())

    new_pixels = []
    for pixel in pixels:
        if data_index < len(binary_msg):
            r, g, b = pixel
            r = (r & ~1) | int(binary_msg[data_index])
            data_index += 1
            if data_index < len(binary_msg):
                g = (g & ~1) | int(binary_msg[data_index])
                data_index += 1
            if data_index < len(binary_msg):
                b = (b & ~1) | int(binary_msg[data_index])
                data_index += 1
            new_pixels.append((r, g, b))
        else:
            new_pixels.append(pixel)

    if data_index < len(binary_msg):
        return None  # message too long

    encoded.putdata(new_pixels)
    out_path = os.path.join(UPLOAD_FOLDER, 'encoded_image.png')
    encoded.save(out_path)
    return out_path

def decode_image(image_path):
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    binary_data = ""
    for pixel in img.getdata():
        for color in pixel[:3]:
            binary_data += str(color & 1)

    decoded = binary_to_text(binary_data)
    if DELIMITER in decoded:
        return decoded[:decoded.index(DELIMITER)]
    return "No hidden message found."

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    image_available = False
    if request.method == "POST":
        if "encode" in request.form:
            uploaded = request.files["image"]
            text = request.form["message"]
            path = os.path.join(UPLOAD_FOLDER, uploaded.filename)
            uploaded.save(path)
            output = encode_image(path, text)
            if output:
                image_available = True
            else:
                message = "❌ Message too large for this image."
        elif "decode" in request.form:
            stego = request.files["stego_image"]
            path = os.path.join(UPLOAD_FOLDER, stego.filename)
            stego.save(path)
            message = decode_image(path)
    return render_template("index.html", message=message, image_available=image_available)

@app.route("/download")
def download():
    file_path = os.path.join(UPLOAD_FOLDER, "encoded_image.png")
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
