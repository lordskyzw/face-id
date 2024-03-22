from pathlib import Path
import logging
from PIL import Image
from uuid import uuid4
from deepface import DeepFace
import shutil
import pandas as pd
from typing import Union, List, Dict, Any, Optional, Tuple

def match_face(image: Union[str, Path], db_path: Union[str, Path]) -> List:
    '''This function takes in an image path and a database path.
    It extracts faces from the image, and for each face extracted, it tries to match it with the faces in the database.
    It then writes the image to the respective directory if a match is found with sufficient confidence.'''

       # Convert string paths to Path objects if necessary
    image = Path(image) if isinstance(image, str) else image
    db_path = Path(db_path) if isinstance(db_path, str) else db_path
    matched_faces_names = []
    # Extract faces from the input image
    faces_detected = DeepFace.extract_faces(
        img_path=str(image),
        detector_backend='yolov8',
        enforce_detection=False
    )

    for face_info in faces_detected:
        '''
        .1) if confidence greater than threshold, crop the face from the image and save it to cropped directory
        .2) compare it with the images in the dataset directory
        .3) if a match is found, write the image to the respective directory and delete the image from the cropped directory'''
        _, facial_area, confidence = face_info['face'], face_info['facial_area'], face_info['confidence']
        if confidence > 0.7:
            # crop the face from the image and save it to cropped directory and return path of the cropped image
            face_image_path = Path('cropped') / f"{uuid4()}.jpg"
            face_image_path.parent.mkdir(exist_ok=True)
            # crop the face
            img = Image.open(image)
            # The facial_area is expected to be a tuple of (x, y, width, height)
            x, y, width, height = facial_area
             # Define a margin (e.g., 10% of the width/height)
            margin_width = int(width * 0.1)
            margin_height = int(height * 0.1)

            # Apply the margin to the cropping area
            left = max(x - margin_width, 0)
            upper = max(y - margin_height, 0)
            right = min(x + width + margin_width, img.width)
            lower = min(y + height + margin_height, img.height)

            cropped_face = img.crop((left, upper, right, lower))

            # Save the cropped face to the cropped directory
            face_image_path = Path('cropped') / f"{uuid4()}.jpg"
            face_image_path.parent.mkdir(exist_ok=True)
            cropped_face.save(face_image_path)
            #TODO find out what happens if you add an unrecognized face
            recognition_results = DeepFace.find(
                img_path=str(face_image_path),
                db_path=str(db_path),
                enforce_detection=False
            )

            # Iterate through each result in the list
            for recognition_result in recognition_results:
                # Check if the result is a DataFrame and not empty
                if isinstance(recognition_result, pd.DataFrame) and not recognition_result.empty:
                    identity = recognition_result.iloc[0]['identity']  # Extract the path of the best match
                    person_name = Path(identity).parent.name  # Extract the person's name from the directory structure

                    # Write the image to the respective directory
                    image_path = db_path / person_name
                    image_path.mkdir(exist_ok=True)

                    # Copy the image to the directory
                    target_path = image_path / image.name
                    with image.open("rb") as img_file:
                        target_content = img_file.read()
                    with open(target_path, "wb") as img_file:
                        img_file.write(target_content)

                    logging.info(f"Image of {person_name} saved to {target_path}")
                    #delete the image from the cropped directory
                    shutil.rmtree(face_image_path)
                    matched_faces_names.append(person_name)
                    break  # Assuming you only want to process the first valid match

    return matched_faces_names