function submitFreemiumPlan() {
    const anthropicApiKey = document.getElementById('anthropicApiKey').value;
    const tavilyApiKey = document.getElementById('tavilyApiKey').value;
    
    fetch('/plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            plan: 'freemium', 
            anthropic_api_key: anthropicApiKey,
            tavily_api_key: tavilyApiKey
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert('Free plan activated successfully!');
        window.location.href = '/keyword';
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('Failed to activate Free plan. Please try again.');
    });
}

function initializePayPalButton(currentPlan) {
    if (currentPlan !== 'premium') {
        paypal.Buttons({
            createOrder: function(data, actions) {
                return actions.order.create({
                    purchase_units: [{
                        amount: {
                            value: '12.00'
                        }
                    }]
                });
            },
            onApprove: function(data, actions) {
                return actions.order.capture().then(function(details) {
                    fetch('/plan', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            plan: 'premium',
                            payment_details: details
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Premium plan activated successfully!');
                        location.reload();
                    })
                    .catch((error) => {
                        console.error('Error:', error);
                        alert('Failed to activate Premium plan. Please try again.');
                    });
                });
            }
        }).render('#paypal-button-container');
    }
}

// Initialize PayPal button when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const currentPlan = document.body.dataset.currentPlan;
    initializePayPalButton(currentPlan);
});