import os
import base64
import numpy as np
import cv2
import json
from deepface import DeepFace
from flask import Flask, request


app = Flask(__name__)

db_path = "dataset"


@app.route('/test', methods=['GET'])
def test():
    return {
        'statusCode': 200,
        'body': json.dumps('Server is running')
    }


@app.route('/add_person', methods=['POST'])
def add_person():
# scenarios to consider
# 1 photo
# multiple photos

# 1 photo
# if its one photo, it could be a photo of a person or a photo with multiple people
    
    
    
    
#this function receives images and adds them to a general folder first 
#then  it extracts faces from the images and attempts to recognize the faces before and save them in a folder(s) with person(s) name(S)
#one picture can contain multiple faces and the function will create a folder for each person
#if the persons name already exists, it adds the new faces to the existing folder
#if the persons name does not exist, it creates a new folder with the persons name
#the function to extract faces is DeepFace.extract_faces()

    req = request.get_json()
    try:
        base_64_image = req['image']
        image_data = base64.b64decode(base_64_image)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        face_detected = DeepFace.extract_faces(img, enforce_detection=False, detector_backend='yolov8')
        unprocessed = "unprocessed"
        
        if len(face_detected)>0:
            # Save the image to the dataset folder
            image_path = f"{db_path}/unprocessed/"
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            cv2.imwrite(f"{image_path}/{unprocessed}_{len(os.listdir(image_path))}.jpg", img)
            for face in face_detected:
                # attempt to recognize the face
                recognition_result = DeepFace.find(img_path=face, db_path=db_path, enforce_detection=False)
                faces_df = recognition_result[0]
                tup = recognition_result[0].shape
                
                if tup[0]>1:
                    identity = faces_df.iloc[0,0]
                    person_name = identity.split('/')[-2]
                    # Save the face to the person's folder
                    image_path = f"{db_path}/{person_name}/"
                    if not os.path.exists(image_path):
                        os.makedirs(image_path)
                    cv2.imwrite(f"{image_path}/{person_name}_{len(os.listdir(image_path))}.jpg", img)
                    
            return {
                'statusCode': 200,
                'body': json.dumps('Person added successfully')
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps('No face detected in the image')
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the image: {str(e)}')
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