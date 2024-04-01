import os
import base64
import json
from fuzzywuzzy import process
from flask import Flask, request, jsonify
from flask_cors import CORS
from mimetypes import guess_type
from pathlib import Path
from uuid import uuid4  
from utils import match_face, update_unrecognized_face_name
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


@app.route('/add_known_person', methods=['POST'])
def add_known_person():
    req = request.get_json()
    images = req.get('images')
    db_path = Path(db_path)  # Define your database directory path here

    if images:
        unprocessed_dir = Path('unprocessed')
        unprocessed_dir.mkdir(parents=True, exist_ok=True)

        all_matched_faces = []
        all_unmatched_faces_ids = []

        for base_64_image in images:
            _, encoded = base_64_image.split(",", 1)
            data = base64.b64decode(encoded)

            unique_filename = f"temp_image_{uuid4()}.jpg"
            image_path = unprocessed_dir / unique_filename

            with open(image_path, 'wb') as f:
                f.write(data)
                logging.info(f'Image saved to {image_path}')

            try:
                matched_faces, unmatched_faces_ids = match_face(image=image_path, db_path=db_path)
                all_matched_faces.extend(matched_faces)
                all_unmatched_faces_ids.extend(unmatched_faces_ids)
                logging.info("Successfully ran match_face() function")
            except Exception as e:
                logging.error(f"ERROR IN match_face() function: {e}")
                return jsonify({'error': f"Error in match_face() function: {e}", 'statusCode': 500})

            os.remove(image_path)

        if all_unmatched_faces_ids:
            # Return the unmatched face IDs for further identification
            return jsonify({'unmatchedFacesIds': all_unmatched_faces_ids, 'matchedFaces': all_matched_faces, 'statusCode': 200})
        else:
            # Every face is matched
            return jsonify({'matchedFaces': all_matched_faces, 'statusCode': 200})

    return jsonify({'error': 'No images provided', 'statusCode': 400})

@app.route('/add_unknown_person', methods=['POST'])
def add_unknown_persons():
    req = request.get_json()
    face_id_name_pairs = req.get('faces')  # Expecting a list of {'id': face_id, 'name': person_name}

    if not face_id_name_pairs:
        return jsonify({'error': 'No data provided', 'statusCode': 400})

    updated_faces = []

    for pair in face_id_name_pairs:
        face_id = pair.get('id')
        person_name = pair.get('name')

        if face_id and person_name:
            update_result = update_unrecognized_face_name(face_id, person_name)
            if update_result:
                updated_faces.append({'id': face_id, 'name': person_name})

    if updated_faces:
        return jsonify({'updatedFaces': updated_faces, 'statusCode': 200})
    else:
        return jsonify({'error': 'Unable to update faces', 'statusCode': 500})


@app.route('/search_person', methods=['POST'])
def search():
    req = request.get_json()
    search_name = req['name']
    dirs = os.listdir(db_path)
    closest_match, score = process.extractOne(search_name, dirs)
    if score > 80:
        image_path = f"{db_path}/{closest_match}/"
        images = os.listdir(image_path)
        base64_images = []
        for image in images:
            mime_type, _ = guess_type(image)
            if mime_type is not None:
                with open(f"{image_path}/{image}", "rb") as img_file:
                    base64_str = base64.b64encode(img_file.read()).decode('utf-8')
                    base64_images.append(f"data:{mime_type};base64,{base64_str}")
        
        return {'images': base64_images}
    else:
        return {
            'statusCode': 404,
            'body': json.dumps('Person not found. No close matches.')
        }


@app.route('/upload', methods=['POST'])
def upload_images():
    req = request.get_json()
    images = req.get('images')
    db_path = Path(db_path)  # Define your database directory path here

    if not images:
        return jsonify({'error': 'No images provided', 'statusCode': 400})

    unprocessed_dir = Path('unprocessed')
    unprocessed_dir.mkdir(parents=True, exist_ok=True)

    all_matched_faces = []
    all_unmatched_faces_data = []  # This will store base64 encoded images for the frontend

    for base_64_image in images:
        _, encoded = base_64_image.split(",", 1)
        data = base64.b64decode(encoded)

        unique_filename = f"temp_image_{uuid4()}.jpg"
        image_path = unprocessed_dir / unique_filename

        with open(image_path, 'wb') as f:
            f.write(data)
            logging.info(f'Image saved to {image_path}')

        try:
            matched_faces, unmatched_faces_info = match_face(image=image_path, db_path=db_path)  # Update match_face to return info needed for frontend
            all_matched_faces.extend(matched_faces)
            all_unmatched_faces_data.extend(unmatched_faces_info)  # Assume this includes base64 data for each face
            logging.info("Successfully ran match_face() function")
        except Exception as e:
            logging.error(f"ERROR IN match_face() function: {e}")
            return jsonify({'error': f"Error in match_face() function: {e}", 'statusCode': 500})

        os.remove(image_path)

    return jsonify({'matchedFaces': all_matched_faces, 'unmatchedFacesData': all_unmatched_faces_data, 'statusCode': 200})

@app.route('/verification', methods=['POST'])
def verify_faces():
    req = request.get_json()
    face_id_name_pairs = req.get('faces')  # Expecting a list of {'id': face_id, 'name': person_name}

    if not face_id_name_pairs:
        return jsonify({'error': 'No data provided', 'statusCode': 400})

    db_path = Path('dataset')  # Define your database directory path here
    updated_faces = []

    for pair in face_id_name_pairs:
        face_id = pair.get('id')
        person_name = pair.get('name')

        if face_id and person_name:
            update_result = update_unrecognized_face_name(face_id, person_name, db_path)
            if update_result:
                updated_faces.append({'id': face_id, 'name': person_name})

    if updated_faces:
        return jsonify({'updatedFaces': updated_faces, 'statusCode': 200})
    else:
        return jsonify({'error': 'Unable to update faces', 'statusCode': 500})



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)