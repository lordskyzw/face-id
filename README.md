
# Face recognition backend

## Requirements
- Python version 3.11

## Step 0: Clone repo and install dependencies
Clone this example project, and change into the directory from the command line.

    $ git clone git@github.com:lordskyzw/face-id.git
    $ cd face-id

Create a virtual environment called `venv`. Activate the virtual environment, and then install the required Python packages inside the virtual environment. If you’re on a Linux or Mac, enter these commands in a terminal.

    $ python3 -m venv face-id
    $ source face-id/bin/activate
    (face-id) $ python3 pip install -r requirements.txt

If you’re on a Windows machine, enter these commands in a command prompt window.

    $ python -m venv face-id
    $ face-id\Scripts\activate
    (face-id) $ pip install -r requirements.txt

## Step 1: Create a custom face recognition dataset
Create a new subfolder inside the `dataset` directory using your first name, like `Tarmica`, to contain your photos.

    (face-id) $ python app.py

This will set up an endpoint which you can interact with using postman for testing purposes or integrate with your own app