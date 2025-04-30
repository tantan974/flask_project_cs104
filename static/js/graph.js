// graps.js
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.download-image-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const imgName = btn.getAttribute('data-img');
            window.location.href = `/download/image/${imgName}`;
        });
    });
});
