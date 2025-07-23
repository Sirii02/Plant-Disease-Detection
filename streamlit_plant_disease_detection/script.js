// Image Preview Function
function previewImage(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('image-preview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Plant Image" style="max-width: 100%; height: auto;">`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = "<p>No image uploaded yet</p>";
    }
}

// Submit Button for Image Upload
async function submitImage() {
    const imageInput = document.getElementById('upload-photo');
    const imageFile = imageInput.files[0];
    
    if (!imageFile) {
        alert("Please upload an image first.");
        return;
    }

    // Create a FormData object and append the image file
    const formData = new FormData();
    formData.append("file", imageFile);

    // Send the image to Google Colab's API for prediction (replace with your ngrok URL)
    try {
        const response = await fetch('http://127.0.0.1:5000/', {  // Replace with actual ngrok URL
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (data.prediction) {
            alert(`The plant is: ${data.prediction}`);
        } else {
            alert("Prediction failed. Please try again.");
        }
    } catch (error) {
        console.error('Error:', error);
        alert("There was an error with the prediction.");
    }
}
