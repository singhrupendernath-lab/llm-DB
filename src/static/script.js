const API_URL = ""; // Relative path as it's served by the same backend
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const reportsList = document.getElementById('reports-list');
const showSqlCheck = document.getElementById('show-sql-check');
const backendStatus = document.getElementById('backend-status');
const backendText = document.getElementById('backend-text');

// Modal elements
const modal = document.getElementById('report-modal');
const modalForm = document.getElementById('modal-form');
const closeModal = document.querySelector('.close-modal');
let currentReportId = null;

// Initialize
async function init() {
    checkHealth();
    loadReports();
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            backendStatus.classList.add('online');
            backendText.innerText = "Online";
        } else {
            throw new Error();
        }
    } catch (e) {
        backendStatus.classList.add('offline');
        backendText.innerText = "Offline";
    }
}

async function loadReports() {
    try {
        const response = await fetch(`${API_URL}/reports`);
        if (!response.ok) throw new Error();

        const reports = await response.json();
        reportsList.innerHTML = '';

        Object.entries(reports).forEach(([id, info]) => {
            const item = document.createElement('div');
            item.className = 'report-item animate-in';
            item.innerHTML = `
                <h4>${id}: ${info.name}</h4>
                <p>${info.description}</p>
            `;
            item.onclick = () => handleReportClick(id, info);
            reportsList.appendChild(item);
        });
    } catch (e) {
        reportsList.innerHTML = '<p class="error">Failed to load reports.</p>';
    }
}

function handleReportClick(id, info) {
    currentReportId = id;

    // Check if the query has variables
    const query = info.query || "";
    const variables = [...new Set(query.match(/[:{](\w+)[}]?/g) || [])]
                      .map(v => v.replace(/[:{}]/g, ''));

    if (variables.length > 0) {
        // Show modal for variables
        document.getElementById('modal-report-title').innerText = info.name;
        document.getElementById('modal-report-desc').innerText = info.description;

        const fields = document.getElementById('modal-fields');
        fields.innerHTML = '';
        variables.forEach(v => {
            const label = document.createElement('label');
            label.innerText = v.charAt(0).toUpperCase() + v.slice(1);
            const input = document.createElement('input');
            input.name = v;
            input.placeholder = `Enter ${v}...`;
            if (v.includes('date')) input.type = 'date';
            fields.appendChild(label);
            fields.appendChild(input);
        });

        modal.style.display = 'block';
    } else {
        // Direct run
        appendMessage('user', `Run report ${id}`);
        askQuestion(`Run report ${id}`);
    }
}

modalForm.onsubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(modalForm);
    let promptText = `Run report ${currentReportId}`;

    formData.forEach((value, key) => {
        if (value) promptText += ` where ${key} is ${value}`;
    });

    modal.style.display = 'none';
    appendMessage('user', promptText);
    askQuestion(promptText);
};

closeModal.onclick = () => modal.style.display = 'none';
window.onclick = (e) => { if (e.target == modal) modal.style.display = 'none'; };

chatForm.onsubmit = async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    userInput.value = '';
    appendMessage('user', text);
    await askQuestion(text);
};

async function askQuestion(question) {
    const assistantMsg = appendMessage('assistant', '<i class="fas fa-spinner fa-spin"></i> Thinking...');

    try {
        const response = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (response.ok) {
            assistantMsg.innerHTML = marked.parse(data.answer);
            if (data.sql_queries && data.sql_queries.length > 0 && showSqlCheck.checked) {
                const sqlDiv = document.createElement('div');
                sqlDiv.className = 'sql-block';
                sqlDiv.innerHTML = '<strong>Executed SQL:</strong>';
                data.sql_queries.forEach(q => {
                    const code = document.createElement('pre');
                    code.innerText = q;
                    sqlDiv.appendChild(code);
                });
                assistantMsg.appendChild(sqlDiv);
            }
        } else {
            assistantMsg.innerText = `Error: ${data.detail || 'Failed to get response'}`;
        }
    } catch (e) {
        assistantMsg.innerText = `Connection error: ${e.message}`;
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role} animate-in`;
    const inner = document.createElement('div');
    inner.className = 'message-content';
    inner.innerHTML = content;
    div.appendChild(inner);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return inner;
}

init();
