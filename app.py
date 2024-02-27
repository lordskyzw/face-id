import json
from deepface import DeepFace
from flask import Flask, request


app = Flask(__name__)

db_path = "dataset"


@app.route('/facial_recognition', methods=['POST'])
def facial_recognition():
    req = request.get_json()
    try:
        base_64_image = req['image']
        face_detected = DeepFace.extract_faces(base_64_image, enforce_detection=False)
    
        if face_detected[0]['confidence']>0.7:
            recognition_result = DeepFace.find(img_path=base_64_image, db_path=db_path, enforce_detection=False)
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
                'body': json.dumps('No face is in the image')
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the image: {str(e)}')
        }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)