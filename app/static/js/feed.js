window.startAnalysis = function(keywordId) {
    sendAnalysisRequest(keywordId, 'Start Analysis');
}

window.refreshAnalysis = function(keywordId) {
    sendAnalysisRequest(keywordId, 'Refresh');
}

function sendAnalysisRequest(keywordId, actionText) {
    const button = document.querySelector(`[data-keyword-id="${keywordId}"]`);
    if (!button) {
        console.error(`Button not found for keyword ID: ${keywordId}`);
        return;
    }

    button.disabled = true;
    
    const statusTextElement = button.querySelector('.status-text');
    if (statusTextElement) {
        statusTextElement.textContent = 'Starting...';
    } else {
        alert('Analysis started!')
        console.warn(`Status text element not found for keyword ID: ${keywordId}`);
    }

    fetch(`/startanalysis/${keywordId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (statusTextElement) {
                statusTextElement.textContent = 'Analyzing...';
            }
            checkStatus(keywordId);
        } else {
            throw new Error(data.message || 'Failed to start analysis');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        console.error('API Endpoint:', `/startanalysis/${keywordId}`);
        console.error('File: feed.js');
        button.disabled = false;
        if (statusTextElement) {
            statusTextElement.textContent = actionText;
        }
        alert(error.message || 'An error occurred. Please try again.');
    });
}

function checkStatus(keywordId) {
    fetch(`/task_status/${keywordId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const button = document.querySelector(`[data-keyword-id="${keywordId}"]`);
            if (!button) {
                console.error(`Button not found for keyword ID: ${keywordId}`);
                return;
            }

            const statusTextElement = button.querySelector('.status-text');

            if (data.status === 'completed') {
                button.disabled = false;
                if (statusTextElement) {
                    statusTextElement.textContent = 'Refresh';
                }
                button.onclick = () => window.refreshAnalysis(keywordId);
                location.reload();
            } else if (data.status === 'failed') {
                throw new Error(data.error_message || 'Analysis failed. Please try again.');
            } else {
                setTimeout(() => checkStatus(keywordId), 5000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const button = document.querySelector(`[data-keyword-id="${keywordId}"]`);
            if (button) {
                button.disabled = false;
                const statusTextElement = button.querySelector('.status-text');
                if (statusTextElement) {
                    statusTextElement.textContent = 'Start Analysis';
                }
                button.onclick = () => window.startAnalysis(keywordId);
            }
            alert(error.message || 'An error occurred while checking status. Please try refreshing the page.');
        });
}
