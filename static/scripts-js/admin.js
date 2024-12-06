function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function checkFiles() {
    const fileInput = document.getElementById('files');
    const files = fileInput.files;

    if (files.length > 100) {
        alert("Вы можете загрузить не более 100 файлов.");
        return false;
    }

    const allowedExtensions = ['txt', 'pdf', 'pptx', 'docx'];
    for (let file of files) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            alert("Можно загружать только файлы форматов: .txt, .pdf, .pptx, .docx");
            return false;
        }
    }

    return true;
}

function handleSubmit() {
    if (checkFiles()) {
        showLoading();
        return true;
    } else {
        return false;
    }
}

const draggables = document.querySelectorAll('.draggable');
const droppables = document.querySelectorAll('.droppable');

draggables.forEach(draggable => {
    draggable.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', JSON.stringify({
            filename: e.target.dataset.filename,
            directory: e.target.dataset.directory
        }));
    });
});

droppables.forEach(droppable => {
    droppable.addEventListener('dragover', (e) => {
        e.preventDefault();
        droppable.classList.add('dragover');
    });

    droppable.addEventListener('dragleave', () => {
        droppable.classList.remove('dragover');
    });

    droppable.addEventListener('drop', async (e) => {
        e.preventDefault();
        droppable.classList.remove('dragover');
        const fileData = JSON.parse(e.dataTransfer.getData('text/plain'));
        const targetDirectory = e.target.dataset.directory;

        if (fileData.directory !== targetDirectory) {
            const response = await fetch('/move_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: fileData.filename,
                    from_directory: fileData.directory,
                    to_directory: targetDirectory
                })
            });

            if (response.ok) {
                window.location.reload();
            } else {
                const result = await response.json();
                alert(`Ошибка: ${result.error}`);
            }
        }
    });
});


const searchInputs = document.querySelectorAll('.search-input');
searchInputs.forEach(input => {
    input.addEventListener('input', function () {
        const directory = this.dataset.dir;
        const searchQuery = this.value.toLowerCase();
        const fileList = document.getElementById(`files-list-${directory}`);
        const files = fileList.querySelectorAll('li');

        files.forEach(file => {
            const fileName = file.textContent.toLowerCase();
            if (fileName.includes(searchQuery)) {
                file.style.display = '';
            } else {
                file.style.display = 'none';
            }
        });
    });
});