import base64
from io import BytesIO
import os, random, string
from PIL import Image
from config import config

def random_alphanumeric(length=10):
    """Generate a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def get_image_base64(image_raw):
    buffered = BytesIO()
    image_raw.save(buffered, format=image_raw.format)
    img_byte = buffered.getvalue()

    return base64.b64encode(img_byte).decode('utf-8')

def file_to_base64(file):
    with open(file, "rb") as f:

        return base64.b64encode(f.read())

def base64_to_image(base64_string):
    base64_string = base64_string.split(",")[1]
    
    return Image.open(BytesIO(base64.b64decode(base64_string)))


def save_uploaded_file(uploaded_file, save_dir):
    """Save the uploaded file to the specified directory."""
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def parse_receipt(uploaded_file):
    import requests

    api_url = f"{config.TRANSCRIPTION_API}/receipt"
    
    # Prepare file and data
    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

    try: 
        response = requests.post(api_url, files=files)
        return response.json()
    except BaseException:
        return None