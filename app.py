import os
import base64
import numpy as np
import cv2
import json
from concurrent.futures import ProcessPoolExecutor
from deepface import DeepFace
from flask import Flask, request
from flask_cors import CORS
from mimetypes import guess_type
from pathlib import Path
from uuid import uuid4  
from utils import match_face
import logging




app = Flask(__name__)
CORS(app) 

db_path = "dataset"


@app.route('/', methods=['GET'])
def test():
    return {
        'statusCode': 200,
        'body': json.dumps('Server is running')
    }


@app.route('/add_person', methods=['POST'])
def add_person():
    req = request.get_json()
    images = req.get('images') 
    
    if images:
        # Ensuring the 'unprocessed' directory exists
        unprocessed_dir = Path('unprocessed')
        unprocessed_dir.mkdir(parents=True, exist_ok=True)
        saved_image_paths = [] 

        for base_64_image in images:
            _, encoded = base_64_image.split(",", 1)
            data = base64.b64decode(encoded)
    
            unique_filename = f"temp_image_{uuid4()}.jpg"
            image_path = unprocessed_dir / unique_filename

            with open(image_path, 'wb') as f:
                f.write(data)
                print(f'Image saved to {image_path}')

            try:
                matchedFaces = match_face(image=image_path, db_path=db_path)
            except Exception as e:
                logging.error(f"ERROR IN match_face() function: {e}")
                return {'error': f"Error in match_face() function{e}", 'statusCode': 500}

            saved_image_paths.append(str(image_path))
            os.remove(image_path)
        
        return {'matchedFaces': matchedFaces, 'statusCode': 200}
            

@app.route('/search_person', methods=['POST'])
def search():
    person_found = False
    req = request.get_json()
    search_name = req['name']
    for dir in os.listdir(db_path):
        if dir.lower() == search_name.lower():
            person_found = True
            image_path = f"{db_path}/{dir}/"
            images = os.listdir(image_path)
            base64_images = []
            for image in images:
                mime_type, _ = guess_type(image)
                if mime_type is not None:
                    with open(f"{image_path}/{image}", "rb") as img_file:
                        base64_str = base64.b64encode(img_file.read()).decode('utf-8')
                        base64_images.append(f"data:{mime_type};base64,{base64_str}")
            
            return {'images': base64_images}
        
    if not person_found:
        return {
            'statusCode': 404,
            'body': json.dumps('Person not found')
        }
    


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable if it's set, otherwise default to 5000
    app.run(debug=False, host='0.0.0.0', port=port)