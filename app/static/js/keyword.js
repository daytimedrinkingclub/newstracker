function showMessage(message, isError = false) {
    const messageElement = document.getElementById('keywordMessage');
    messageElement.textContent = message;
    messageElement.className = `mt-2 text-sm ${isError ? 'text-red-600' : 'text-green-600'}`;
    setTimeout(() => {
        messageElement.textContent = '';
        messageElement.className = 'mt-2 text-sm';
    }, 3000);
}

function addKeyword() {
    const keyword = document.getElementById('newKeyword').value;
    if (!keyword) {
        showMessage('Please enter a keyword', true);
        return;
    }

    fetch('/keyword', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `keyword=${encodeURIComponent(keyword)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Keyword added successfully');
            location.reload();
        } else {
            showMessage('Failed to add keyword: ' + data.error, true);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred while adding the keyword', true);
    });
}

function deleteKeyword(id) {
    if (confirm('Are you sure you want to delete this keyword?')) {
        fetch(`/keyword/${id}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showMessage('Keyword deleted successfully');
                location.reload();
            } else {
                showMessage('Failed to delete keyword: ' + (data.error || 'Unknown error'), true);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred while deleting the keyword', true);
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const newKeywordInput = document.getElementById('newKeyword');
    if (newKeywordInput) {
        newKeywordInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                addKeyword();
            }
        });
    }
});