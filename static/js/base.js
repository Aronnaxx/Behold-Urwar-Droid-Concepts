// Common utility functions
const utils = {
    // Format a number to a specified number of decimal places
    formatNumber: (number, decimals = 2) => {
        return Number(number).toFixed(decimals);
    },

    // Format a file size in bytes to a human-readable string
    formatFileSize: (bytes) => {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${utils.formatNumber(size)} ${units[unitIndex]}`;
    },

    // Debounce a function to limit its execution rate
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Show a notification message
    showNotification: (message, type = 'info') => {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    },

    // Handle API errors
    handleApiError: (error) => {
        console.error('API Error:', error);
        let message = 'An error occurred. Please try again.';

        if (error.response) {
            // Server responded with error status
            message = error.response.data.message || message;
        } else if (error.request) {
            // Request made but no response
            message = 'No response from server. Please check your connection.';
        }

        utils.showNotification(message, 'error');
        return Promise.reject(error);
    }
};

// Form validation
const formValidation = {
    // Validate required fields
    validateRequired: (form) => {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('error');
                isValid = false;
            } else {
                field.classList.remove('error');
            }
        });

        return isValid;
    },

    // Validate numeric input
    validateNumeric: (input, min, max) => {
        const value = Number(input.value);
        if (isNaN(value) || value < min || value > max) {
            input.classList.add('error');
            return false;
        }
        input.classList.remove('error');
        return true;
    },

    // Add validation to a form
    addValidation: (form) => {
        form.addEventListener('submit', (e) => {
            if (!formValidation.validateRequired(form)) {
                e.preventDefault();
                utils.showNotification('Please fill in all required fields', 'error');
            }
        });
    }
};

// File upload handling
const fileUpload = {
    // Handle file selection
    handleFileSelect: (input, previewElement) => {
        const file = input.files[0];
        if (!file) return;

        // Update preview
        if (previewElement) {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewElement.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                previewElement.textContent = file.name;
            }
        }

        // Show file size
        utils.showNotification(`Selected file: ${file.name} (${utils.formatFileSize(file.size)})`);
    },

    // Add file upload handling to an input
    addFileUpload: (input, previewElement) => {
        input.addEventListener('change', () => {
            fileUpload.handleFileSelect(input, previewElement);
        });
    }
};

// Initialize common functionality
document.addEventListener('DOMContentLoaded', () => {
    // Add validation to all forms
    document.querySelectorAll('form').forEach(form => {
        formValidation.addValidation(form);
    });

    // Add file upload handling to all file inputs
    document.querySelectorAll('input[type="file"]').forEach(input => {
        const preview = input.nextElementSibling?.classList.contains('preview') 
            ? input.nextElementSibling 
            : null;
        fileUpload.addFileUpload(input, preview);
    });

    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}); 