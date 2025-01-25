let mediaRecorder;
let audioChunks = [];
let audioBlob;

document.getElementById("startBtn").addEventListener("click", startRecording);
document.getElementById("stopBtn").addEventListener("click", stopRecording);
document.getElementById("playbackBtn").addEventListener("click", playbackOriginalAudio);
document.getElementById("saveBtn").addEventListener("click", saveAudio);
document.getElementById("uploadBtn").addEventListener("click", uploadAudio);
document.getElementById("transcribeBtn").addEventListener("click", transcribeAudio);

function transcribeAudio() {
    fetch('/transcribe', {
        method: 'POST'
    }).then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
    }).then(data => {
        const transcriptionText = document.getElementById("transcriptionText");
        if (data.transcription) {
            transcriptionText.innerText = data.transcription; // Set the transcription text
            transcriptionText.hidden = false; // Show the transcription section
        } else {
            transcriptionText.innerText = "Transcription error: " + data.error;
            transcriptionText.hidden = false; // Show the error message
        }
    }).catch(error => {
        console.error("Error during transcription:", error);
        const transcriptionText = document.getElementById("transcriptionText");
        transcriptionText.innerText = "An error occurred during transcription.";
        transcriptionText.hidden = false; // Show the error message
    });
}

async function startRecording() {
    audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
    mediaRecorder.onstop = () => {
        audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        toggleButtons(true, false, true, true, true); // Enable Transcribe button after recording
    };

    mediaRecorder.start();
    toggleButtons(false, true, false, false);
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }
    toggleButtons(true, false, true, true);
}

function playbackOriginalAudio() {
    const audioURL = URL.createObjectURL(audioBlob);
    const originalPlayback = document.getElementById("originalPlayback");
    originalPlayback.src = audioURL;
    originalPlayback.hidden = false;
    document.getElementById("originalLabel").hidden = false;
    originalPlayback.play();
}

function saveAudio() {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");

    fetch('/save_audio', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
    }).then(data => {
        alert(data.message);
        toggleButtons(true, false, true, true, true);  // Enable Transcribe button after saving
    }).catch(error => {
        console.error("Error saving audio:", error);
        alert("An error occurred while saving the audio.");
    });
}

function uploadAudio() {
    document.getElementById("progress").hidden = false;

    fetch('/enhance', {
        method: 'POST'
    }).then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        return response.blob();
    }).then(blob => {
        document.getElementById("progress").hidden = true;

        const audioURL = URL.createObjectURL(blob);
        const enhancedPlayback = document.getElementById("enhancedPlayback");
        enhancedPlayback.src = audioURL;
        enhancedPlayback.hidden = false;
        document.getElementById("enhancedLabel").hidden = false;
        enhancedPlayback.play();
        
        // Optional download link creation
        const downloadBtn = document.createElement("a");
        downloadBtn.href = audioURL;
        downloadBtn.download = "enhanced_recording.wav";
        downloadBtn.innerText = "Download Enhanced Audio";
        downloadBtn.classList.add("download-btn");
        document.body.appendChild(downloadBtn);
        downloadBtn.style.display = "inline-block";

    }).catch(error => {
        document.getElementById("progress").hidden = true;
        console.error("Error enhancing audio:", error);
        alert("An error occurred while enhancing the audio.");
    });
}

function toggleButtons(startEnabled, stopEnabled, playbackEnabled, saveUploadEnabled, transcribeEnabled = false) {
    document.getElementById("startBtn").disabled = !startEnabled;
    document.getElementById("stopBtn").disabled = !stopEnabled;
    document.getElementById("playbackBtn").disabled = !playbackEnabled;
    document.getElementById("saveBtn").disabled = !saveUploadEnabled;
    document.getElementById("uploadBtn").disabled = !saveUploadEnabled;
    document.getElementById("transcribeBtn").disabled = !transcribeEnabled; // Set Transcribe button based on parameter
}
