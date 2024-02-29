from pathlib import Path
from deepface import DeepFace
import numpy as np
from typing import Union, List, Dict, Any, Optional, Tuple

def match_face(image: Path, db_path: Path) -> None:
    '''This function takes in an image path and a database path.
    It extracts faces from the image, and for each face extracted, it tries to match it with the faces in the database.
    It then writes the image to the respective directory if a match is found with sufficient confidence.'''

    # Extract faces from the input image
    faces_detected = DeepFace.extract_faces(
        img_path=str(image), 
        detector_backend='yolov8', 
        enforce_detection=False,
        target_size=(224, 224),
        align=True,
        expand_percentage=0,
        grayscale=False
    )

    for face_info in faces_detected:
        face, facial_area, confidence = face_info['face'], face_info['facial_area'], face_info['confidence']
        if confidence > 0.5:
            # Look for a match in the database
            recognition_result = DeepFace.find(
                img_path=str(image), 
                db_path=str(db_path), 
                enforce_detection=False
            )

            # Check if there are any matches
            if not recognition_result.empty:
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

                print(f"Image of {person_name} saved to {target_path}")
