// ============================================
// SmartDine - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips and popovers
    initializeBootstrapFeatures();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize dynamic features
    initializeDynamicFeatures();
    
    // Initialize cart utilities
    initializeCartUtilities();
}

/**
 * Initialize Bootstrap tooltips and popovers
 */
function initializeBootstrapFeatures() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize dynamic features
 */
function initializeDynamicFeatures() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.remove('show');
            alert.classList.add('fade');
        }, 5000);
    });
    
    // Enable form select change event triggers
    const formSelects = document.querySelectorAll('form .form-select');
    formSelects.forEach(function (select) {
        select.addEventListener('change', function () {
            if (this.hasAttribute('data-auto-submit')) {
                this.closest('form').submit();
            }
        });
    });
    
    // Confirm before destructive actions
    const dangerButtons = document.querySelectorAll('[data-confirm]');
    dangerButtons.forEach(function (button) {
        button.addEventListener('click', function (e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initialize cart utilities
 */
function initializeCartUtilities() {
    // Update cart count display
    updateCartCount();
    
    // Validate quantity selections
    const quantitySelects = document.querySelectorAll('select[name="quantity"]');
    quantitySelects.forEach(function (select) {
        select.addEventListener('change', function () {
            if (this.value < 1) {
                this.value = 1;
            }
        });
    });
}

/**
 * Update cart count in navigation
 */
function updateCartCount() {
    const cartCount = document.querySelector('.navbar .badge');
    if (cartCount) {
        const count = parseInt(cartCount.textContent) || 0;
        if (count > 0) {
            cartCount.classList.remove('d-none');
        }
    }
}

/**
 * Format currency values
 */
function formatCurrency(value) {
    return '₹' + parseFloat(value).toFixed(2);
}

/**
 * Format date to readable format
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Show loading spinner
 */
function showLoader(element) {
    if (!element) return;
    const loader = document.createElement('div');
    loader.className = 'spinner';
    element.appendChild(loader);
}

/**
 * Hide loading spinner
 */
function hideLoader(element) {
    if (!element) return;
    const spinner = element.querySelector('.spinner');
    if (spinner) {
        spinner.remove();
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.position = 'fixed';
    container.style.top = '80px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone number format
 */
function isValidPhone(phone) {
    const phoneRegex = /^[0-9]{10}$/;
    return phoneRegex.test(phone.replace(/\D/g, ''));
}

/**
 * Calculate order total with tax
 */
function calculateOrderTotal(subtotal, taxPercentage = 18) {
    const tax = (subtotal * taxPercentage) / 100;
    return subtotal + tax;
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * AJAX request helper
 */
function makeAjaxRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => resolve(data))
            .catch(error => reject(error));
    });
}

/**
 * Get CSRF token from cookie
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Filter table rows based on search input
 */
function filterTableRows(tableId, searchInputId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('keyup', debounce(function () {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    }, 300));
}

/**
 * Highlight table row on hover
 */
function highlightTableRows(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.addEventListener('mouseenter', function () {
            this.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
        });
        row.addEventListener('mouseleave', function () {
            this.style.backgroundColor = '';
        });
    });
}

/**
 * Export table to CSV
 */
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        let rowData = [];
        const cells = row.querySelectorAll('td, th');
        cells.forEach(cell => {
            rowData.push('"' + cell.textContent.trim().replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    downloadCSV(csv.join('\n'), filename);
}

/**
 * Download CSV file
 */
function downloadCSV(content, filename) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(content));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

/**
 * Print page
 */
function printPage() {
    window.print();
}

/**
 * Smooth scroll to element
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Add loading state to button
 */
function setButtonLoading(button, isLoading = true) {
    if (isLoading) {
        button.disabled = true;
        button.setAttribute('data-original-text', button.innerHTML);
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text');
    }
}

// Export functions for global use
window.SmartDine = {
    formatCurrency,
    formatDate,
    showLoader,
    hideLoader,
    showToast,
    isValidEmail,
    isValidPhone,
    calculateOrderTotal,
    debounce,
    makeAjaxRequest,
    getCookie,
    filterTableRows,
    highlightTableRows,
    exportTableToCSV,
    downloadCSV,
    printPage,
    scrollToElement,
    isInViewport,
    setButtonLoading
};
