window.startAnalysis = function(keywordId) {
    sendAnalysisRequest(keywordId, 'Start Analysis');
}

window.refreshAnalysis = function(keywordId) {
    sendAnalysisRequest(keywordId, 'Refresh');
}

function sendAnalysisRequest(keywordId, actionText) {
    const button = document.querySelector(`[data-keyword-id="${keywordId}"]`);
    button.disabled = true;
    button.querySelector('.status-text').textContent = 'Starting...';

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
            button.querySelector('.status-text').textContent = 'Analyzing...';
            checkStatus(keywordId);  // Note: we're now passing keywordId instead of job_id
        } else {
            throw new Error(data.message || 'Failed to start analysis');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.disabled = false;
        button.querySelector('.status-text').textContent = actionText;
        alert(error.message || 'An error occurred. Please try again.');
    });
}
    fetch(`/task_status/${keywordId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const button = document.querySelector(`[data-keyword-id="${keywordId}"]`);
            if (data.status === 'completed') {
                button.disabled = false;
                button.querySelector('.status-text').textContent = 'Refresh';
                button.onclick = () => window.refreshAnalysis(keywordId);
                location.reload(); // Reload the page to show updated summary
            } else if (data.status === 'failed') {
                throw new Error(data.error_message || 'Analysis failed. Please try again.');
            } else {
                // Check again after 5 seconds
                setTimeout(() => checkStatus(keywordId), 5000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const button = document.querySelector(`[data-keyword-id="${keywordId}"]`);
            button.disabled = false;
            button.querySelector('.status-text').textContent = 'Start Analysis';
            button.onclick = () => window.startAnalysis(keywordId);
            alert(error.message || 'An error occurred while checking status. Please try refreshing the page.');
        });
        });
