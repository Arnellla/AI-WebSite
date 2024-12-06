
const textarea = document.getElementById('user-input');
const submitButton = document.querySelector('form button[type="submit"]');
const chatBox = document.getElementById('chat-box');
const documentSelect = document.getElementById('document-select');

const scrollDownBtn = document.getElementById('scroll-down-btn');

function setCookie(name, value, days) {
    const d = new Date();
    d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + d.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith(name + '=')) {
            return cookie.substring(name.length + 1);
        }
    }
    return "";
}

function saveCheckboxState() {
    const documentCheckboxes = document.querySelectorAll('.document-checkbox');
    const directoryCheckboxes = document.querySelectorAll('.directory-checkbox');

    const state = {};

    documentCheckboxes.forEach(checkbox => {
        state[checkbox.value] = checkbox.checked;
    });

    directoryCheckboxes.forEach(directoryCheckbox => {
        const fileCheckboxes = directoryCheckbox.closest('details').querySelectorAll('.document-checkbox');
        const allChecked = Array.from(fileCheckboxes).every(fileCheckbox => fileCheckbox.checked);
        directoryCheckbox.checked = allChecked;
        state[directoryCheckbox.value] = directoryCheckbox.checked;
    });

    localStorage.setItem('checkboxState', JSON.stringify(state));
}

function restoreCheckboxState() {
    const savedState = localStorage.getItem('checkboxState');
    if (savedState) {
        const state = JSON.parse(savedState);

        const documentCheckboxes = document.querySelectorAll('.document-checkbox');
        const directoryCheckboxes = document.querySelectorAll('.directory-checkbox');

        documentCheckboxes.forEach(checkbox => {
            checkbox.checked = state[checkbox.value] !== undefined ? state[checkbox.value] : true;
        });

        directoryCheckboxes.forEach(directoryCheckbox => {
            directoryCheckbox.checked = state[directoryCheckbox.value] !== undefined ? state[directoryCheckbox.value] : true;
        });
    } else {
        document.querySelectorAll('.document-checkbox, .directory-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
    }
}


function setupDirectoryCheckboxSync() {
    document.querySelectorAll('.directory-checkbox').forEach(directoryCheckbox => {
        directoryCheckbox.addEventListener('change', function () {
            const isChecked = this.checked;
            const fileCheckboxes = this.closest('details').querySelectorAll('.document-checkbox');

            fileCheckboxes.forEach(fileCheckbox => {
                fileCheckbox.checked = isChecked;
            });
            saveCheckboxState();
        });
    });


    document.querySelectorAll('.document-checkbox').forEach(documentCheckbox => {
        documentCheckbox.addEventListener('change', function () {
            const directoryCheckbox = this.closest('details').querySelector('.directory-checkbox');
            const fileCheckboxes = this.closest('details').querySelectorAll('.document-checkbox');

            const allChecked = Array.from(fileCheckboxes).every(fileCheckbox => fileCheckbox.checked);
            directoryCheckbox.checked = allChecked;

            saveCheckboxState();
        });
    });
}


document.addEventListener('DOMContentLoaded', () => {
    restoreCheckboxState();
    setupDirectoryCheckboxSync();
});


textarea.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('chat-form').requestSubmit();
    }
});


function addLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'bot', 'loading');

    const loader = document.createElement('div');
    loader.classList.add('loader');

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        loader.appendChild(dot);
    }

    loadingDiv.appendChild(loader);
    chatBox.prepend(loadingDiv);

    return loadingDiv;
}

function removeLoadingIndicator(loadingElement) {
    loadingElement?.remove();
}

function toggleSettingsPanel(show) {
    settingsPanel.classList.toggle('show', show);
}

const settingsBtn = document.getElementById('settings-btn');
const settingsPanel = document.getElementById('settings-panel');

settingsBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleSettingsPanel(!settingsPanel.classList.contains('show'));
});

document.addEventListener('click', (e) => {
    if (!settingsPanel.contains(e.target) && !settingsBtn.contains(e.target)) {
        toggleSettingsPanel(false);
    }
});

let touchStartY = 0;
let touchEndY = 0;

document.addEventListener('touchstart', (e) => {
    touchStartY = e.changedTouches[0].screenY;
});

document.addEventListener('touchmove', (e) => {
    touchEndY = e.changedTouches[0].screenY;
});

document.addEventListener('touchend', handleTouchEvent);



function isUserAtBottom() {
    return chatBox.scrollTop + chatBox.clientHeight >= chatBox.scrollHeight;
}



chatBox.addEventListener('scroll', function () {
    if (!isUserAtBottom()) {
        scrollDownBtn.style.display = 'flex';
    } else {
        scrollDownBtn.style.display = 'none';
    }
});

scrollDownBtn.addEventListener('click', function () {
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
    scrollDownBtn.style.display = 'none';
});

document.addEventListener("DOMContentLoaded", async function () {
    const documentContainer = document.getElementById('file-list-container');
    const searchInput = document.getElementById('search-input');

    try {
        const response = await fetch('/get_files');
        const directoryStructure = await response.json();

        let allFilesHTML = '';
        const displayedFiles = new Set();

        for (const directory in directoryStructure) {
            if (directory === "" || directory === "family&&&&&&&&") {
                continue;
            }

            let directoryFilesHTML = `
            <details>
                <summary>
                    <input type="checkbox" class="directory-checkbox" value="${directory}">
                    ${directory}
                </summary>
                <ul>`;

            directoryStructure[directory].forEach(file => {
                const baseFileName = file.replace(/_chap\d+/, '').replace(/\.[^/.]+$/, "");

                const isDisplayed = displayedFiles.has(baseFileName);

                directoryFilesHTML += `
                <li style="${isDisplayed ? 'display: none;' : ''}"> 
                    <label>
                        <input type="checkbox" name="documents" class="document-checkbox" data-base-name="${baseFileName}" value="${directory}/${file}">
                        ${baseFileName}
                        <a href="/view_file/${baseFileName}" class="view-link" target="_blank">Перейти</a>
                    </label>
                </li>`;

                displayedFiles.add(baseFileName);
            });

            directoryFilesHTML += '</ul></details>';
            allFilesHTML += directoryFilesHTML;
        }

        documentContainer.innerHTML = allFilesHTML;

        restoreCheckboxState();

        document.querySelectorAll('.document-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function () {
                const baseFileName = this.dataset.baseName;

                document.querySelectorAll(`.document-checkbox[data-base-name="${baseFileName}"]`).forEach(cb => {
                    cb.checked = this.checked;
                });

                saveCheckboxState();
            });
        });

        searchInput.addEventListener('input', function () {
            const searchText = searchInput.value.toLowerCase();

            document.querySelectorAll('#file-list-container li').forEach(item => {
                const fileName = item.textContent.toLowerCase();
                if (fileName.includes(searchText)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });

            document.querySelectorAll('#file-list-container details').forEach(directory => {
                const files = directory.querySelectorAll('li');
                const hasVisibleFiles = Array.from(files).some(file => file.style.display !== 'none');
                directory.style.display = hasVisibleFiles ? '' : 'none';
            });
        });

        document.querySelectorAll('.directory-checkbox').forEach(directoryCheckbox => {
            directoryCheckbox.addEventListener('change', function () {
                const isChecked = this.checked;
                const fileCheckboxes = this.closest('details').querySelectorAll('.document-checkbox');
                fileCheckboxes.forEach(fileCheckbox => {
                    fileCheckbox.checked = isChecked;
                });
                saveCheckboxState();
            });
        });

        document.querySelectorAll('.document-checkbox').forEach(documentCheckbox => {
            documentCheckbox.addEventListener('change', function () {
                const directoryCheckbox = this.closest('details').querySelector('.directory-checkbox');
                const fileCheckboxes = this.closest('details').querySelectorAll('.document-checkbox');

                const allChecked = Array.from(fileCheckboxes).every(fileCheckbox => fileCheckbox.checked);
                directoryCheckbox.checked = allChecked;
            });
        });

    } catch (error) {
        console.error('Ошибка при загрузке списка документов:', error);
    }

    try {
        const response = await fetch('/get_chat_history', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            const messages = data.messages;

            if (messages && messages.length > 0) {
                messages.forEach(msg => {
                    const sender = msg[1] === 'user' ? 'user' : 'bot';
                    const text = msg[0];

                    addMessageToChat(sender, text, isMarkdown = true);
                });
            }
        } else {
            console.error('Не удалось загрузить историю сообщений');
        }
    } catch (error) {
        console.error('Ошибка при загрузке истории сообщений:', error);
    }
});






function handleTouchEvent(e) {
    touchEndY = e.changedTouches[0].screenY;

    const documentList = document.getElementById('file-list-container');
    const isDocumentListScrolling = documentList.scrollTop + documentList.clientHeight < documentList.scrollHeight;

    if (!isDocumentListScrolling && !isUserAtBottom() && touchEndY - touchStartY > 50) {
        toggleSettingsPanel(false);
    }
}












textarea.addEventListener('input', function () {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;

    submitButton.disabled = !textarea.value.trim();
});

document.getElementById('chat-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    const input = textarea.value.trim();


    const selectedDocuments = Array.from(document.querySelectorAll('.document-checkbox:checked'))
        .map(checkbox => checkbox.value);


    const selectedDirectories = Array.from(document.querySelectorAll('.directory-checkbox:checked'))
        .map(checkbox => checkbox.value);

    if (input !== '' && (selectedDocuments.length > 0 || selectedDirectories.length > 0)) {
        addMessageToChat('user', input);
        textarea.value = '';
        textarea.style.height = 'auto';

        document.getElementById('chat-form').style.display = 'none';

        const loadingElement = addLoadingIndicator();

        try {
            const response = await sendMessageToServer(input, selectedDocuments, selectedDirectories);

            removeLoadingIndicator(loadingElement);

            if (response && response.response) {
                addMessageToChat('bot', response.response, true);
            } else if (response && response.error) {
                console.error('Ошибка сервера:', response.error);
                addMessageToChat('bot', `Ошибка сервера: ${response.error}`);
            } else {
                throw new Error('Не удалось получить ответ от сервера.');
            }
        } catch (error) {
            console.error(error);
            addMessageToChat('bot', error.message || 'Произошла ошибка при обработке сообщения.');
        } finally {
            document.getElementById('chat-form').style.display = 'flex';
            textarea.focus();
        }
    } else {
        addMessageToChat('bot', 'Пожалуйста, выберите документы для анализа.');
    }
});







function addMessageToChat(sender, text, isMarkdown = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    if (isMarkdown) {
        const htmlContent = DOMPurify.sanitize(marked.parse(text.replace('<br>')));

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;

        const tables = tempDiv.querySelectorAll('table');
        if (tables.length > 0) {
            tables.forEach(table => {
                const tableContainer = document.createElement('div');
                tableContainer.classList.add('table-container');
                table.parentNode.insertBefore(tableContainer, table);
                tableContainer.appendChild(table);
            });
            messageDiv.innerHTML = tempDiv.innerHTML;
        } else {
            messageDiv.innerHTML = htmlContent;
        }
    } else {
        messageDiv.textContent = text;
    }

    chatBox.prepend(messageDiv);
    const links = messageDiv.querySelectorAll('a');
    links.forEach(link => {
        link.setAttribute('target', '_blank');
    });
}



async function sendMessageToServer(message, selectedDocument, selectedDirectories) {
    const username = getCookie('username');

    if (!username) {
        console.error('Имя пользователя не найдено в куки');
        return;
    }

    const payload = {
        message,
        document: selectedDocument,
        directories: selectedDirectories,
        username
    };

    console.log('Отправляем данные на сервер:', payload);

    try {
        const response = await fetch('/send_message_new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            return await response.json();
        } else {
            const errorData = await response.json();
            console.error('Ошибка сервера:', errorData);
            return null;
        }
    } catch (error) {
        console.error('Ошибка при отправке сообщения:', error);
        return null;
    }
}

document.getElementById('admin-btn').addEventListener('click', function () {
    window.open('/admin', '_blank');
});

document.getElementById('logout-btn').addEventListener('click', function () {
    document.cookie.split(";").forEach(function(c) {
        document.cookie = c.trim().split("=")[0] + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/";
    });
    window.location.href = '/';
});

