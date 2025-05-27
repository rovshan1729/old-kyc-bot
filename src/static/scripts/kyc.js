document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('keyup', searchTable);

    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
    }

    document.addEventListener('click', (event) => {
        const modal = document.getElementById('downloadModal');
        const btn = document.querySelector('.download-btn');
        if (!modal.contains(event.target) && !btn.contains(event.target)) {
            modal.classList.remove('active');
        }
    });
});

function searchTable() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('.document-row');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function toggleDownloadModal() {
    const modal = document.getElementById('downloadModal');
    modal.classList.toggle('active');
}

function downloadExcel() {
    window.location.href = '/kyc/download_excel';
    toggleDownloadModal();
}

function downloadPDF() {
    window.location.href = '/kyc/download_pdf_all';
    toggleDownloadModal();
}

function downloadJSON() {
    window.location.href = '/kyc/download_json';
    toggleDownloadModal();
}

function downloadAllZips() {
    window.location.href = '/kyc/download_all_zips';
    toggleDownloadModal();
}

function downloadUserPDF(userId) {
    window.location.href = `/kyc/download_pdf/${userId}`;
}

function showPreviewModal(userId, filename) {
    const modal = document.getElementById('previewModal');
    const previewContent = document.getElementById('previewContent');
    const downloadBtn = document.getElementById('downloadBtn');
    const url = `/kyc/verifier_data/${userId}/${encodeURIComponent(filename)}`;

    previewContent.innerHTML = '';
    if (filename.endsWith('.jpg')) {
        const img = document.createElement('img');
        img.src = url;
        previewContent.appendChild(img);
    } else if (filename.endsWith('.mp4')) {
        const video = document.createElement('video');
        video.src = url;
        video.controls = true;
        previewContent.appendChild(video);
    }

    downloadBtn.onclick = () => {
        window.location.href = url;
    };

    modal.style.display = 'flex';
}

function closePreview() {
    const modal = document.getElementById('previewModal');
    modal.style.display = 'none';
}