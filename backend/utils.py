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
import base64
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db_uri = os.environ.get("MONGO_URL")
db_path = Path("dataset")

def store_unrecognized_face(face_image_path: Path, full_image_path: Path, face_id: str, db):
    '''Store the unmatched cropped face image and its full version along with ID in MongoDB.'''
    #make sure face_image_path and full_image_path are Path objects and create them if they don't exist
    face_image_path = Path(face_image_path) if isinstance(face_image_path, str) else face_image_path
    full_image_path = Path(full_image_path) if isinstance(full_image_path, str) else full_image_path
    # create the directories if they don't exist
    face_image_path.parent.mkdir(parents=True, exist_ok=True)
    full_image_path.parent.mkdir(parents=True, exist_ok=True)
    logging.info(f"=============Directories created are {face_image_path.parent} and {full_image_path.parent}================================")
    with open(face_image_path, "rb") as image_file:
        encoded_cropped_image = Binary(image_file.read())  # Encode the image file to binary format for MongoDB
    with open(full_image_path, "rb") as full_image:
        encoded_full_image = Binary(full_image.read())
    # Insert the face ID and the binary data into the MongoDB collection
    db.unmatched_faces.insert_one({"face_id": str(face_id), "cropped_and_full_path": (encoded_cropped_image, encoded_full_image)})

def update_unrecognized_face_name(face_id: str, person_name: str, db_path: Union[str, Path], db_uri=db_uri, db_name="faceid") -> bool:
    '''Update the name for an unrecognized face in the MongoDB database and move the picture to the named directory.'''
    
    # Ensure db_path is a Path object
    db_path = Path(db_path) if isinstance(db_path, str) else db_path

    # Connect to MongoDB
    client = pymongo.MongoClient(db_uri)
    db = client[db_name]

    # The collection where unmatched faces are stored
    unmatched_faces_collection = db.unmatched_faces

    # Find the document for the given face_id
    face_document = unmatched_faces_collection.find_one({"face_id": face_id})

    if face_document:
        # Retrieve the binary data for cropped and full images
        cropped_image_data, full_image_data = face_document['cropped_and_full_path']

        # Create a directory for the person if it doesn't exist
        person_dir = db_path / person_name
        person_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Person directory created: {person_dir}")

        # Write the cropped and full images to files in the person's directory
        cropped_image_path = person_dir / f"{face_id}_cropped.jpg"
        full_image_path = person_dir / f"{face_id}_full.jpg"

        with open(cropped_image_path, 'wb') as cropped_file:
            cropped_file.write(cropped_image_data)
        with open(full_image_path, 'wb') as full_file:
            full_file.write(full_image_data)

        logging.info(f"Images for {person_name} saved to directory: {person_dir}")

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
    unmatched_faces_data = []

    # Extract faces from the input image
    faces_detected = DeepFace.extract_faces(
        img_path=str(image_path),
        detector_backend='yolov8',
        enforce_detection=False
    )
    logging.info(f"amount of Faces detected: {len(faces_detected)}") #faces_detected is a list of dictionaries 
    i=0
        
    for face_info in faces_detected:
        #logging.info(f"face_info structure: {face_info}")  # Add this line to inspect face_info
        try:
            facial_area= faces_detected[i]['facial_area']
            confidence = faces_detected[i]['confidence']
            
        except ValueError as e:
            logging.error(f"Error unpacking face_info: {e}, face_info: {face_info}")
            continue
        if confidence > 0.7:
            # Crop the face from the image and save it to cropped directory
            img = Image.open(image_path)
            x, y, width, height = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
            margin_width = int(width * 0.1)
            margin_height = int(height * 0.1)

            left = max(x - margin_width, 0)
            upper = max(y - margin_height, 0)
            right = min(x + width + margin_width, img.width)
            lower = min(y + height + margin_height, img.height)

            cropped_face = img.crop((left, upper, right, lower))
            face_image_path = Path('cropped') / f"{uuid4()}.jpg"
            
            #create the directory if it doesn't exist
            face_image_path.parent.mkdir(parents=True, exist_ok=True)
            cropped_face.save(face_image_path)
            logging.info(f"Face saved to {face_image_path}")
            logging.info(f"running DeepFace.find() on {face_image_path}")

            # Attempt to find a match in the database
            recognition_results = DeepFace.find(
                img_path=str(face_image_path),
                db_path=str(db_path),
                enforce_detection=False
            )
            logging.info("ran DeepFace.find()")
            logging.info(f"Recognition results type: {type(recognition_results)}")
            logging.info(f"Recognition results: {recognition_results}")
            #later find the shape of the recognition_results if its an ndarray

            if len(recognition_results) > 0:

                for df in recognition_results:

                    if not df.empty:

                        for index, row in df.iterrows():

                            identity = row['identity']
                            distance = row['distance']

                            if distance < 0.25:
                                # Match found, handle the recognized face
                                logging.info("Match found for the face")
                                person_name = Path(identity).stem  # Extract the person's name from the file name
                                logging.info(f"Matched with {person_name}")

                                # Write the image to the respective directory
                                person_dir = db_path / person_name
                                person_dir.mkdir(exist_ok=True)
                                shutil.copy(face_image_path, person_dir / face_image_path.name)

                                logging.info(f"Image of {person_name} saved to {person_dir / face_image_path.name}")
                                matched_faces_names.append(person_name)
                                break
                            else:
                                logging.info("No match found for the face")
                                # For unmatched faces, store both full image and cropped face
                                face_id = uuid4()
                                unmatched_faces_ids.append(str(face_id))  # Store as string for JSON compatibility

                                store_unrecognized_face(face_image_path, image_path, str(face_id), db)  # Ensure IDs are strings
                                logging.info(f"Unmatched face stored with ID: {face_id}, in MongoDB")

                                # Convert cropped face to base64 for frontend
                                buffered = BytesIO()
                                cropped_face.save(buffered, format="JPEG")
                                encoded_cropped_face = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                unmatched_faces_data.append({'id': str(face_id), 'image': encoded_cropped_face})
                    else:
                        logging.info("df is empty")
                        
        else:
            logging.info(f"Face confidence is less than 0.7, skipping face {i}")
        i+=1


    client.close()
    #unmatched_faces_data is a list of dictionaries each dictionary containing the id(for use to extract the full image in the db) and the base64 of the cropped face for front end to verify
    # while matched_faces_names is a list of strings
    return matched_faces_names, unmatched_faces_data 
