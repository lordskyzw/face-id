import os
import pymongo
import shutil
import logging
from pathlib import Path
from PIL import Image
from uuid import uuid4
from deepface import DeepFace
from typing import Union, List
from bson.binary import Binary


db_uri = os.environ.get("MONGO_URL")
db_path = Path("dataset")

def store_unrecognized_face(face_image_path: Path, full_image_path: Path, face_id: str, db):
    '''Store the unmatched cropped face image and its full version along with ID in MongoDB.'''
    with open(face_image_path, "rb") as image_file:
        encoded_cropped_image = Binary(image_file.read())  # Encode the image file to binary format for MongoDB
    with open(full_image_path, "rb") as full_image:
        encoded_full_image = Binary(full_image.read())
    db.unmatched_faces.insert_one({"face_id": str(face_id), "cropped_and_full_path": (encoded_cropped_image, encoded_full_image)})

def update_unrecognized_face_name(face_id: str, person_name: str, db_path: Union[str, Path], db_uri=db_uri, db_name="faceid") -> bool:
    '''Update the name for an unrecognized face in the MongoDB database and move the picture to the named directory.'''
    db_path = Path(db_path) if isinstance(db_path, str) else db_path
    client = pymongo.MongoClient(db_uri)
    db = client[db_name]

    # The collection where unmatched faces are stored
    unmatched_faces_collection = db.unmatched_faces

    # Find the document for the given face_id
    face_document = unmatched_faces_collection.find_one({"face_id": face_id})

    if face_document:
        # Retrieve the image binary data
        image_data = face_document['image']

        # Create a directory for the person if it doesn't exist
        person_dir = db_path / person_name
        person_dir.mkdir(parents=True, exist_ok=True)

        # Write the image data to a file in the person's directory
        image_path = person_dir / f"{face_id}.jpg"
        with open(image_path, 'wb') as image_file:
            image_file.write(image_data)
        logging.info(f"==================added {person_name} to DIRECTORY: {person_dir}")
        # Optionally, delete the document from MongoDB after processing
        unmatched_faces_collection.delete_one({"face_id": face_id})

        client.close()  # Close the MongoDB connection
        return True
    else:
        client.close()  # Close the MongoDB connection
        return False

def match_face(image: Union[str, Path], db_path: Union[str, Path]=db_path, db_uri=db_uri, db_name="faceid") -> List:
    '''This function takes in an image path and a database path.
    It extracts faces from the image, and for each face extracted, it tries to match it with the faces in the database.
    Unmatched faces are stored in MongoDB with a unique ID.'''
    
    # MongoDB setup
    client = pymongo.MongoClient(db_uri)
    db = client[db_name]

    # Convert string paths to Path objects if necessary
    image_path = Path(image) if isinstance(image, str) else image
    db_path = Path(db_path) if isinstance(db_path, str) else db_path
    matched_faces_names = []
    unmatched_faces_ids = []

    # Extract faces from the input image
    faces_detected = DeepFace.extract_faces(
        img_path=str(image_path),
        detector_backend='yolov8',
        enforce_detection=False
    )

    for face_info in faces_detected:
        face, facial_area, confidence = face_info['face'], face_info['facial_area'], face_info['confidence']
        if confidence > 0.7:
            # Crop the face from the image and save it to cropped directory
            img = Image.open(image_path)
            x, y, width, height = facial_area
            margin_width = int(width * 0.1)
            margin_height = int(height * 0.1)

            left = max(x - margin_width, 0)
            upper = max(y - margin_height, 0)
            right = min(x + width + margin_width, img.width)
            lower = min(y + height + margin_height, img.height)

            cropped_face = img.crop((left, upper, right, lower))
            face_image_path = Path('cropped') / f"{uuid4()}.jpg"
            cropped_face.save(face_image_path)

            # Attempt to find a match in the database
            recognition_results = DeepFace.find(
                img_path=str(face_image_path),
                db_path=str(db_path),
                enforce_detection=False
            )

            if not recognition_results.empty:
                # Match found, handle the recognized face
                identity = recognition_results.iloc[0]['identity']  # Extract the path of the best match
                person_name = Path(identity).stem  # Extract the person's name from the file name

                # Write the image to the respective directory
                person_dir = db_path / person_name
                person_dir.mkdir(exist_ok=True)
                shutil.copy(face_image_path, person_dir / face_image_path.name)

                logging.info(f"Image of {person_name} saved to {person_dir / face_image_path.name}")
                matched_faces_names.append(person_name)

                # Delete the cropped image
                face_image_path.unlink()
            else:
                logging.info("====unrecognized faces detected within the picture====")
                face_id = uuid4()
                unmatched_faces_ids.append(face_id)

                # Store the face and its ID in MongoDB
                store_unrecognized_face(face_image_path, image_path, face_id, db)


    client.close()  # Close the MongoDB connection
    return matched_faces_names, unmatched_faces_ids
