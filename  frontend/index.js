document.getElementById('search-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

        // Clear existing images immediately when a new search begins
    const imageGrid = document.getElementById('image-grid');
    imageGrid.innerHTML = '';

    const searchName = document.getElementById('search-input').value;

    fetch('https://face-id.up.railway.app/search_person', {
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
    fetch('http://localhost:5000/add_person', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ images: images }) // Make sure the key matches with the server-side
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to send images.');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response:', data);
    })
    .catch(error => {
        console.error('Error:', error.message);
    })
    .finally(() => {
        // Clear the array after uploading
        base64Images = [];
        updateDropCounter(); // Reset drop counter
        uploadButton.setAttribute('disabled', 'disabled');
    });
}

function updateDropCounter() {
    document.getElementById('drop-counter').textContent = `Dropped ${base64Images.length} photo(s)`;
}

document.getElementById('dark-mode-toggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
});
