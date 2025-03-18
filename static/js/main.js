// Main JavaScript file for common functionality

// Dark mode toggle
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved dark mode preference
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        document.body.classList.add('dark-mode');
    }

    // Add dark mode toggle button if it doesn't exist
    if (!document.getElementById('dark-mode-toggle')) {
        const toggle = document.createElement('button');
        toggle.id = 'dark-mode-toggle';
        toggle.className = 'btn btn-outline-secondary position-fixed bottom-0 end-0 m-3';
        toggle.innerHTML = '<i class="fas fa-moon"></i>';
        toggle.onclick = function() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        };
        document.body.appendChild(toggle);
    }
});

// Common utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// AJAX form submission
function submitForm(form, url, options = {}) {
    if (!validateForm(form)) {
        showNotification('Please fill in all required fields', 'danger');
        return;
    }

    const formData = new FormData(form);
    
    fetch(url, {
        method: options.method || 'POST',
        body: formData,
        ...options
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Operation successful', 'success');
            if (options.onSuccess) options.onSuccess(data);
        } else {
            showNotification(data.error || 'Operation failed', 'danger');
        }
    })
    .catch(error => {
        showNotification('An error occurred: ' + error, 'danger');
    });
}

// Export common functions
window.showNotification = showNotification;
window.validateForm = validateForm;
window.submitForm = submitForm; 
