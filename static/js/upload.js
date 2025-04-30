// upload.js

// Wait for the page to load
document.addEventListener('DOMContentLoaded', function () {
    // Find the drop area for file uploads
    const dropArea = document.querySelector('.drop-area');
    if (!dropArea) return;

    // Highlight drop area when file is dragged over
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.classList.add('highlight');
    });

    // Remove highlight when drag leaves
    dropArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropArea.classList.remove('highlight');
    });

    // Handle file drop
    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.classList.remove('highlight');
        const files = e.dataTransfer.files;
        // Set dropped files to the file input
        if (files.length) {
            document.querySelector('input[type="file"]').files = files;
        }
    });
});
