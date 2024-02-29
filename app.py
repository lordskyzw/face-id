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
    images = req.get('images')  # This should be an array of base64-encoded strings
    
    if images:
        for base_64_image in images:
            # Assume the base64 string is complete with the necessary header
            header, encoded = base_64_image.split(",", 1)
            data = base64.b64decode(encoded)
            
            # You can now save this data to a file or process it further
            # For example, let's write it to a temporary file
            with open('unprocessed/temp_image.jpg', 'wb') as f:
                f.write(data)
                print('Image saved to temp_image.jpg')
            
            # Now you can use DeepFace to process the image
            # faces = DeepFace.extract_faces(img_path = 'temp_image.jpg', ...)
            # Process the faces as needed

            # Make sure to remove the temporary file if you're done with it
            #os.remove('temp_image.jpg')

        return {'status': 'success'}, 200
    else:
        return {'error': 'No images provided'}, 400


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
    


@app.route('/facial_recognition', methods=['POST'])
def facial_recognition():
    req = request.get_json()
    try:
        base_64_image = req['image']
        image_data = base64.b64decode(base_64_image)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        face_detected = DeepFace.extract_faces(img, enforce_detection=False, detector_backend='yolov8')
    
        if face_detected[0]['confidence']>0.5:
            recognition_result = DeepFace.find(img_path=img, db_path=db_path, enforce_detection=False)
            faces_df = recognition_result[0]
            tup = recognition_result[0].shape
            
            if tup[0]>1:
                identity = faces_df.iloc[0,0]  # Extract the person's name
                person_name = identity.split('/')[-2]
                return {
                    'statusCode': 200,
                    'body': json.dumps(f'Person identified: {person_name}')
                }
            else:
                # Face not recognized
                return {
                    'statusCode': 200,
                    'body': json.dumps('Unknown human detected')
                }
        else:
            # No face detected
            return {
                'statusCode': 200,
                'body': json.dumps(f'No face is in the image also confidence is {face_detected[0]["confidence"]}')
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the image: {str(e)}')
        }


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable if it's set, otherwise default to 5000
    app.run(debug=False, host='0.0.0.0', port=port)