
//let currentResolveValue = null;
let isWaiting = false;
let tempX = 0; // Last click coordinate in Image


eel.expose(open_crop_popup);
function open_crop_popup(img_b64, transcript, all_transcript) {
    // Open Modal
    const modal = document.getElementById('cropModal');
    modal.style.display = 'flex';
    
    document.getElementById('cropImage').src = "data:image/png;base64," + img_b64;
    document.getElementById('allTranscriptLabel').innerText = all_transcript;
    document.getElementById('transcriptLabel').innerText = transcript;

    // reset guide line
    const line = document.getElementById('guideLine');
    line.style.display = 'none';
    tempX = 0;

    //currentResolveValue = null; // Resetta il valore
    isWaiting = true;

    return null
}

function confirmCrop() {
    const modal = document.getElementById('cropModal');
    modal.style.display = 'none';
    isWaiting = false;

    eel.return_split_value(tempX);
}

function cancelProcess() {
    if (confirm("Do you really want to stop the whole segmentation? Unsaved progress will be lost.")) {
        document.getElementById('cropModal').style.display = 'none';
        // Send cancel=true to Python
        eel.return_split_value(0, true);
    }
}


function handleImageClick(event) {
    const img = event.target;
    const rect = img.getBoundingClientRect();
    
    // Compuete X coordinate in original image scale
    const scaleX = img.naturalWidth / rect.width;
    tempX = Math.round((event.clientX - rect.left) * scaleX);

    // Put a vertical Line
    const line = document.getElementById('guideLine');
    const relativeX = event.clientX - rect.left; 
    
    line.style.left = relativeX + 'px';
    line.style.display = 'block';

    console.log("Clicked X coordinate in original image scale:", tempX);
}

window.addEventListener('keydown', function(event) {
    // if Modal is open and user press Enter, confirm the crop
    if (document.getElementById('cropModal').style.display === 'flex') {
        if (event.key === "Enter") {
            confirmCrop();
        }
    }
});