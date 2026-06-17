document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.querySelector('input[name="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            const fileName = e.target.files[0]?.name || '';
            const label = document.querySelector('label[for="file"]');
            if (label) {
                label.textContent = fileName ? `${fileName}` : 'Upload image';
            }
        });
    }

    const filesInput = document.querySelector('input[name="files"]');
    const filesContainer = document.createElement('div');
    filesContainer.id = 'file-list';
    if (filesInput) {
        filesInput.parentNode.insertBefore(filesContainer, filesInput.nextSibling);
        filesInput.addEventListener('change', function (e) {
            const files = e.target.files;
            let html = '';
            if (files.length > 0) {
                html = '<ul style="margin-top:0.5rem; list-style: none; padding-left:0;">';
                for (let i = 0; i < files.length; i++) {
                    html += `<li>${files[i].name} (${(files[i].size / 1024).toFixed(1)} KB)</li>`;
                }
                html += '</ul>';
            }
            filesContainer.innerHTML = html;
        });
    }

    const archiveForm = document.querySelector('form[action="/archive"]');
    if (archiveForm) {
        archiveForm.addEventListener('submit', function (e) {
            const files = document.querySelector('input[name="files"]');
            if (files && files.files.length === 0) {
                e.preventDefault();
                alert('Please select at least one file.');
            }
        });
    }

    const imageForm = document.querySelector('form[action="/image"]');
    if (imageForm) {
        imageForm.addEventListener('submit', function (e) {
            const file = document.querySelector('input[name="file"]');
            if (file && file.files.length === 0) {
                e.preventDefault();
                alert('Please select an image file.');
            }
        });
    }
});