document.addEventListener('DOMContentLoaded', () => {
    console.log("Voxir JS loaded");

    const ttsButton = document.getElementById('tts-button');
    const ttsInput = document.getElementById('tts-input');
    const ttsAudio = document.getElementById('tts-audio');

    if (ttsButton) {
        ttsButton.addEventListener('click', async () => {
            const text = ttsInput.value.trim();
            if (!text) {
                alert('Please enter some text.');
                return;
            }

            ttsButton.disabled = true;
            ttsButton.textContent = 'Converting...';
            ttsAudio.src = ''; // Clear previous audio

            try {
                const response = await fetch('/api/tts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text }),
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const audioUrl = URL.createObjectURL(blob);
                    ttsAudio.src = audioUrl;
                    ttsAudio.hidden = false;
                    ttsAudio.load(); // Preload audio
                    // ttsAudio.play(); // Optionally autoplay
                } else {
                    const errorData = await response.json();
                    console.error('TTS API error:', errorData);
                    displayError(ttsAudio.parentElement, `TTS Error: ${errorData.error || response.statusText}`);
                    ttsAudio.hidden = true;
                }
            } catch (error) {
                console.error('TTS fetch error:', error);
                displayError(ttsAudio.parentElement, 'An error occurred while converting text to speech.');
                ttsAudio.hidden = true;
            } finally {
                ttsButton.disabled = false;
                ttsButton.textContent = 'Convert to Speech';
            }
        });
    }

    const imageToSpeechButton = document.getElementById('image-to-speech-button');
    const imageUploadInput = document.getElementById('image-upload');
    const imageAudio = document.getElementById('image-audio');

    if (imageToSpeechButton) {
        imageToSpeechButton.addEventListener('click', async () => {
            const file = imageUploadInput.files[0];
            if (!file) {
                alert('Please select an image file.');
                return;
            }

            imageToSpeechButton.disabled = true;
            imageToSpeechButton.textContent = 'Processing...';
            imageAudio.src = ''; // Clear previous audio
            imageAudio.hidden = true;

            const formData = new FormData();
            formData.append('image', file);

            try {
                const response = await fetch('/api/image-to-speech', {
                    method: 'POST',
                    body: formData, // No 'Content-Type' header needed for FormData with fetch
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const audioUrl = URL.createObjectURL(blob);
                    imageAudio.src = audioUrl;
                    imageAudio.hidden = false;
                    imageAudio.load();
                } else {
                    const errorData = await response.json();
                    console.error('Image-to-Speech API error:', errorData);
                    displayError(imageAudio.parentElement, `Image-to-Speech Error: ${errorData.error || response.statusText}`);
                    imageAudio.hidden = true;
                }
            } catch (error) {
                console.error('Image to speech fetch error:', error);
                displayError(imageAudio.parentElement, 'An error occurred while processing the image.');
                imageAudio.hidden = true;
            } finally {
                imageToSpeechButton.disabled = false;
                imageToSpeechButton.textContent = 'Convert Image to Speech';
            }
        });
    }

    const textToVideoButton = document.getElementById('text-to-video-button');
    const videoTextInput = document.getElementById('video-text-input');
    const videoOutputDiv = document.getElementById('video-output');

    if (textToVideoButton) {
        textToVideoButton.addEventListener('click', async () => {
            const text = videoTextInput.value.trim();
            if (!text) {
                alert('Please enter some text for the video.');
                return;
            }

            textToVideoButton.disabled = true;
            textToVideoButton.textContent = 'Generating Video...';
            videoOutputDiv.innerHTML = '<p>Processing, please wait...</p>'; // Clear previous video & show message

            try {
                const response = await fetch('/api/text-to-video', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text }),
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const videoUrl = URL.createObjectURL(blob);

                    videoOutputDiv.innerHTML = ''; // Clear processing message
                    const videoPlayer = document.createElement('video');
                    videoPlayer.src = videoUrl;
                    videoPlayer.controls = true;
                    videoPlayer.width = 640; // Or some other appropriate size
                    videoPlayer.height = 360;
                    videoOutputDiv.appendChild(videoPlayer);
                    videoPlayer.load();

                } else {
                    const errorData = await response.json();
                    alert(`Error: ${errorData.error || response.statusText}`);
                    videoOutputDiv.innerHTML = `<p style="color: red;">Error: ${errorData.error || response.statusText}</p>`;
                }
            } catch (error) {
                console.error('Text to video fetch error:', error);
                alert('An error occurred while generating the video.');
                videoOutputDiv.innerHTML = '<p style="color: red;">An error occurred while generating the video.</p>';
            } finally {
                textToVideoButton.disabled = false;
                textToVideoButton.textContent = 'Convert to Video';
            }
        });
    }

    // Helper function to display errors within a given parent element
    function displayError(parentElement, message) {
        // Remove existing error messages
        const existingError = parentElement.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        const errorElement = document.createElement('p');
        errorElement.textContent = message;
        errorElement.className = 'error-message';
        errorElement.style.color = 'red';
        errorElement.style.fontSize = '0.9em';
        parentElement.appendChild(errorElement); // Append to the section
    }

    // Clear error messages when input changes (optional UX improvement)
    [ttsInput, imageUploadInput, videoTextInput].forEach(input => {
        if (input) {
            input.addEventListener('input', () => {
                const section = input.closest('section');
                if (section) {
                    const existingError = section.querySelector('.error-message');
                    if (existingError) {
                        existingError.remove();
                    }
                }
            });
        }
    });
});
