document.getElementById('search-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

        // Clear existing images immediately when a new search begins
    const imageGrid = document.getElementById('image-grid');
    imageGrid.innerHTML = '';

    const searchName = document.getElementById('search-input').value;

    fetch('https://face-id-production.up.railway.app/search_person', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: searchName })
    })
    .then(response => {
        if (!response.ok) {
            // If the response is not okay, check if it's because the person was not found
            if(response.status === 404) {
                showModal('No person found with the provided name.');
            } else {
                // For other types of errors
                throw new Error('Search failed.');
            }
            // If the response isn't ok, we don't want to continue processing the response as JSON
            throw new Error('Response not OK.');
        }
        return response.json();
    })
    .then(data => {
        // This will only be reached if the response was ok (2xx status code)
        handleResponse(data); // Handle the data normally
    })
    .catch(error => {
        console.error('Error:', error.message);
        // showModal('Failed to search person.'); // Only if you want to show modal for every error
    });
});


function handleResponse(responseData) {
    // Clear existing images
    const imageGrid = document.getElementById('image-grid');
    imageGrid.innerHTML = '';

    // Check if images are present in the response
    if (responseData.images && responseData.images.length > 0) {
        // Display images in a grid
        responseData.images.forEach(imageData => {
            const img = document.createElement('img');
            img.src = imageData; // Assuming imageData is a complete data URI
            img.classList.add('image-grid-item');
            imageGrid.appendChild(img);
        });
    } else {
        // No images found, show an alert
        showModal('No person found with the provided name.');
    }
}
function showModal(message) {
    document.getElementById('modal-text').textContent = message;
    document.getElementById('modal').classList.remove('hidden');
}
function closeModal() {
    document.getElementById('modal').classList.add('hidden');
}

const dropArea = document.getElementById('drop-area');
const fileUpload = document.getElementById('file-upload');
const uploadButton = document.getElementById('upload-button');
let base64Images = [];

dropArea.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropArea.classList.add('bg-gray-100');
});

dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('bg-gray-100');
});

dropArea.addEventListener('drop', (event) => {
    event.preventDefault();
    dropArea.classList.remove('bg-gray-100');
    
    const files = event.dataTransfer.files;

    for (const file of files) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            base64Images.push(reader.result);
            updateDropCounter();
            uploadButton.removeAttribute('disabled');
        };
    }
});

fileUpload.addEventListener('change', (event) => {
    const files = event.target.files;

    for (const file of files) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            base64Images.push(reader.result);
            updateDropCounter();
            uploadButton.removeAttribute('disabled');
        };
    }
});

uploadButton.addEventListener('click', () => {
    if (base64Images.length > 0) {
        sendImages(base64Images);
    } else {
        alert('Please drop photos first.');
    }
});

function sendImages(images) {
    fetch('https://face-id-production.up.railway.app/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ images: images })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to send images.');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response:', data);

        // Handle matched faces with a modal
        if (data.matchedFaces.length > 0) {
            const matchedNames = data.matchedFaces.join(', ');
            showModal(`Matched Faces: ${matchedNames}`);
        }

        // Handle unmatched faces
        const unmatchedContainer = document.getElementById('unmatchedFacesContainer');
        if (data.unmatchedFacesData.length > 0) {
            unmatchedContainer.classList.remove('hidden'); // Show the container
        } else {
            unmatchedContainer.classList.add('hidden'); // Ensure it's hidden if there are no unmatched faces
        }

        unmatchedContainer.innerHTML = ''; // Clear previous unmatched faces
        data.unmatchedFacesData.forEach(face => {
            const faceDiv = document.createElement('div');
            faceDiv.setAttribute('data-face-id', face.id);
            const img = new Image();
            img.src = `data:image/jpeg;base64,${face.image}`;
            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = 'Enter name';
            input.required = true;

            const confirmButton = document.createElement('button');
            confirmButton.textContent = 'Confirm';
            confirmButton.onclick = function() {
                if (input.value.trim() !== '') {
                    // Send the name and face ID to the validation endpoint
                    confirmFaceName(face.id, input.value);
                } else {
                    // Optionally, alert the user or handle the empty input case gracefully
                    console.error('Name is required'); // Log an error or alert the user
                    // For a better user experience, consider adding a visual indication that the input is required
                    input.classList.add('input-required'); // Example: add a class that styles the border in red
                }
            };

            faceDiv.appendChild(img);
            faceDiv.appendChild(input);
            faceDiv.appendChild(confirmButton);
            unmatchedContainer.appendChild(faceDiv);
        });
    })
    .catch(error => {
        console.error('Error:', error.message);
    })
    .finally(() => {
        // Clear the array after uploading
        base64Images = []; // Make sure this variable is defined in your script
        updateDropCounter(); // Make sure this function is defined in your script
        const uploadButton = document.getElementById('uploadButton');
        uploadButton.setAttribute('disabled', 'disabled');
    });
}

function showModal(text) {
    const modal = document.getElementById("myModal");
    const modalText = document.getElementById("modalText");
    const span = document.getElementsByClassName("close")[0];

    modalText.innerText = text;
    modal.style.display = "block";

    // When the user clicks on <span> (x), close the modal
    span.onclick = function() {
        modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
}



function confirmFaceName(faceId, name) {
    const verificationUrl = 'https://face-id-production.up.railway.app/verification';

    fetch(verificationUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ faces: [{ face_id: faceId, name: name }] })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Verification Response:', data);
        
        // Assume successful response includes an array of updatedFaces
        if (data.updatedFaces && data.updatedFaces.length > 0) {
            // Remove the divs for the verified faces
            data.updatedFaces.forEach(face => {
                const faceDiv = document.querySelector(`div[data-face-id="${face.id}"]`);
                if (faceDiv) {
                    faceDiv.remove();  // Remove the div from the DOM
                }
            });

            // Show a pop-up indicating success
            alert("Person(s) added successfully!");
        } else {
            // Handle the case where no faces were updated successfully
            alert("No faces were added. Please try again.");
        }
    })
    .catch(error => {
        console.error('Verification Error:', error);
        alert("An error occurred during verification. Please try again.");
    });
}


function updateDropCounter() {
    document.getElementById('drop-counter').textContent = `Dropped ${base64Images.length} photo(s)`;
}

document.getElementById('dark-mode-toggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
});
