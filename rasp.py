import cv2
import face_recognition
import serial
import time

# Serial communication with Arduino
arduino_port = '/dev/ttyUSB0'  # Change this to your Arduino port
arduino_baudrate = 9600
arduino_connection = serial.Serial(arduino_port, arduino_baudrate, timeout=1)

# Function to send unlock signal to Arduino
def unlock_door():
    arduino_connection.write(b'1')  # Send '1' to Arduino

# Function to capture frames from cameras and perform facial recognition
def facial_recognition(camera_indexes):
    video_capture = [cv2.VideoCapture(index) for index in camera_indexes]

    known_face_encoding = ...  # Load the known face encoding from your dataset

    while True:
        for i, cap in enumerate(video_capture):
            ret, frame = cap.read()
            if not ret:
                print(f"Error reading frame from camera {i}")
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding in face_encodings:
                # Check if the face matches the known face
                matches = face_recognition.compare_faces([known_face_encoding], face_encoding)
                if True in matches:
                    print(f"Face recognized on camera {i}")
                    unlock_door()  # Send unlock signal to Arduino

            # Display the frame with face rectangles (for debugging)
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            cv2.imshow(f"Camera {i}", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    for cap in video_capture:
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        # Provide the indexes of the cameras you want to use
        # e.g., [0, 1] for cameras with indexes 0 and 1
        camera_indexes = [0, 1]

        facial_recognition(camera_indexes)

    except KeyboardInterrupt:
        print("Script terminated by user.")

    finally:
        arduino_connection.close()
