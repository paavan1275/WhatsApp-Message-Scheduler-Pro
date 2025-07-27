document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('messageForm');
    const repeatCheckbox = document.getElementById('repeat');
    const repeatOptions = document.getElementById('repeatOptions');
    const submitBtn = document.getElementById('submitBtn');
    const alertsContainer = document.getElementById('alerts-container');

    // Toggle repeat options
    repeatCheckbox.addEventListener('change', function() {
        repeatOptions.classList.toggle('show', this.checked);
    });

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        submitBtn.classList.add('loading');
        
        // Get form data
        const formData = {
            numbers: document.getElementById('numbers').value,
            message: document.getElementById('message').value,
            time: document.getElementById('time').value,
            repeat: repeatCheckbox.checked,
            interval: document.getElementById('interval').value,
            count: document.getElementById('count').value
        };

        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('success', data.success || 'Messages scheduled successfully!');
                form.reset();
                repeatOptions.classList.remove('show');
            } else {
                showAlert('error', data.error || 'An error occurred');
            }
        } catch (error) {
            showAlert('error', 'Network error. Please try again.');
            console.error('Error:', error);
        } finally {
            submitBtn.classList.remove('loading');
        }
    });

    function showAlert(type, message) {
        // Clear existing alerts
        alertsContainer.innerHTML = '';
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alert.style.animation = 'pop 0.3s ease-out';
        
        alertsContainer.appendChild(alert);
        
        // Remove alert after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'fadeIn 0.3s ease-out reverse';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }

    // Input validation for phone numbers
    document.getElementById('numbers').addEventListener('input', function(e) {
        const value = e.target.value;
        // Basic validation for international numbers
        if (value && !/^(\+\d+[\s,]*)+$/.test(value)) {
            this.setCustomValidity('Please enter numbers in international format (+countrycode) separated by commas');
        } else {
            this.setCustomValidity('');
        }
    });
});
