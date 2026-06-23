/**
 * InvoiceHubNet - Premium JavaScript Framework
 * Built by Quick Red Tech Software Development Studio
 */

(function() {
    'use strict';

    // ==================== Utility Functions ====================
    
    const Utils = {
        // Format currency
        formatCurrency(amount, currency = 'NGN') {
            const symbols = {
                'NGN': '₦',
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'KES': 'KSh',
                'ZAR': 'R',
                'GHS': '₵'
            };
            const symbol = symbols[currency] || '₦';
            return `${symbol}${parseFloat(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        },

        // Format date
        formatDate(date, format = 'short') {
            const d = new Date(date);
            const options = {
                short: { year: 'numeric', month: 'short', day: 'numeric' },
                long: { year: 'numeric', month: 'long', day: 'numeric' },
                full: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
            };
            return d.toLocaleDateString('en-US', options[format] || options.short);
        },

        // Debounce function
        debounce(func, wait) {
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

        // Generate invoice number
        generateInvoiceNumber(prefix = 'INV') {
            const date = new Date();
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
            return `${prefix}-${year}${month}${day}-${random}`;
        },

        // Validate email
        isValidEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },

        // Get file extension
        getFileExtension(filename) {
            return filename.split('.').pop().toLowerCase();
        }
    };

    // ==================== Theme Manager ====================
    
    const ThemeManager = {
        init() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            this.setTheme(savedTheme);
            
            // Listen for system preference changes
            if (window.matchMedia) {
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                    if (!localStorage.getItem('theme')) {
                        this.setTheme(e.matches ? 'dark' : 'light');
                    }
                });
            }
        },

        setTheme(theme) {
            document.body.classList.remove('light', 'dark');
            document.body.classList.add(theme === 'dark' ? 'dark-mode' : '');
            localStorage.setItem('theme', theme);
            
            const toggleBtn = document.querySelector('[data-theme-toggle]');
            if (toggleBtn) {
                toggleBtn.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
            }
        },

        toggle() {
            const currentTheme = localStorage.getItem('theme') || 'light';
            this.setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        }
    };

    // ==================== Toast Notifications ====================
    
    const Toast = {
        container: null,

        init() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info', duration = 5000) {
            this.init();
            
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const icons = {
                success: 'fa-check',
                error: 'fa-times',
                warning: 'fa-exclamation',
                info: 'fa-info'
            };
            
            toast.innerHTML = `
                <div class="toast-icon">
                    <i class="fas ${icons[type] || icons.info}"></i>
                </div>
                <div class="toast-content">
                    <div class="toast-message">${message}</div>
                </div>
                <button class="toast-close" onclick="Toast.dismiss(this.parentElement)">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            this.container.appendChild(toast);
            
            // Auto dismiss
            if (duration > 0) {
                setTimeout(() => this.dismiss(toast), duration);
            }
            
            return toast;
        },

        dismiss(toast) {
            toast.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
            }, 300);
        },

        success(message, duration) { return this.show(message, 'success', duration); },
        error(message, duration) { return this.show(message, 'error', duration); },
        warning(message, duration) { return this.show(message, 'warning', duration); },
        info(message, duration) { return this.show(message, 'info', duration); }
    };

    // ==================== Modal Manager ====================
    
    const Modal = {
        open(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        },

        close(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        },

        init() {
            // Close on overlay click
            document.querySelectorAll('.modal-overlay').forEach(overlay => {
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        overlay.classList.remove('active');
                        document.body.style.overflow = '';
                    }
                });
            });

            // Close on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                        modal.classList.remove('active');
                    });
                    document.body.style.overflow = '';
                }
            });
        }
    };

    // ==================== Invoice Calculator ====================
    
    const InvoiceCalculator = {
        calculate() {
            const items = document.querySelectorAll('.invoice-item');
            let subtotal = 0;

            items.forEach(item => {
                const quantity = parseFloat(item.querySelector('.item-quantity')?.value) || 0;
                const unitPrice = parseFloat(item.querySelector('.item-price')?.value) || 0;
                const total = quantity * unitPrice;
                
                const totalEl = item.querySelector('.item-total');
                if (totalEl) {
                    totalEl.textContent = Utils.formatCurrency(total, document.getElementById('currency')?.value || 'NGN');
                }
                
                subtotal += total;
            });

            const discountPercent = parseFloat(document.getElementById('discount_percent')?.value) || 0;
            const taxPercent = parseFloat(document.getElementById('tax_percent')?.value) || 0;
            const shipping = parseFloat(document.getElementById('shipping_amount')?.value) || 0;

            const discountAmount = subtotal * (discountPercent / 100);
            const taxAmount = (subtotal - discountAmount) * (taxPercent / 100);
            const total = subtotal - discountAmount + taxAmount + shipping;

            // Update display
            const subtotalEl = document.getElementById('subtotal');
            const discountEl = document.getElementById('discount_amount');
            const taxEl = document.getElementById('tax_amount');
            const shippingEl = document.getElementById('shipping_display');
            const totalEl = document.getElementById('grand_total');

            const currency = document.getElementById('currency')?.value || 'NGN';

            if (subtotalEl) subtotalEl.textContent = Utils.formatCurrency(subtotal, currency);
            if (discountEl) discountEl.textContent = `-${Utils.formatCurrency(discountAmount, currency)}`;
            if (taxEl) taxEl.textContent = Utils.formatCurrency(taxAmount, currency);
            if (shippingEl) shippingEl.textContent = Utils.formatCurrency(shipping, currency);
            if (totalEl) totalEl.textContent = Utils.formatCurrency(total, currency);
        },

        init() {
            // Calculate on input change
            document.addEventListener('input', Utils.debounce(() => this.calculate(), 300));
            
            // Initial calculation
            this.calculate();
        }
    };

    // ==================== Dynamic Invoice Rows ====================
    
    const InvoiceRows = {
        addItem() {
            const container = document.getElementById('invoice-items');
            const template = document.getElementById('invoice-item-template');
            
            if (template) {
                const html = template.innerHTML;
                const div = document.createElement('div');
                div.innerHTML = html;
                const newItem = div.firstElementChild;
                container.appendChild(newItem);
                this.initItemEvents(newItem);
            }
        },

        removeItem(button) {
            const item = button.closest('.invoice-item');
            const items = document.querySelectorAll('.invoice-item');
            
            if (items.length > 1) {
                item.remove();
                InvoiceCalculator.calculate();
            } else {
                Toast.warning('At least one item is required.');
            }
        },

        initItemEvents(item) {
            const quantityInput = item.querySelector('.item-quantity');
            const priceInput = item.querySelector('.item-price');
            
            if (quantityInput) {
                quantityInput.addEventListener('input', Utils.debounce(() => InvoiceCalculator.calculate(), 300));
            }
            
            if (priceInput) {
                priceInput.addEventListener('input', Utils.debounce(() => InvoiceCalculator.calculate(), 300));
            }
        },

        init() {
            // Add item button
            const addBtn = document.getElementById('add-item-btn');
            if (addBtn) {
                addBtn.addEventListener('click', () => this.addItem());
            }

            // Initialize existing items
            document.querySelectorAll('.invoice-item').forEach(item => this.initItemEvents(item));
        }
    };

    // ==================== Form Validation ====================
    
    const FormValidator = {
        validate(form) {
            let isValid = true;
            const errors = [];

            // Check required fields
            form.querySelectorAll('[required]').forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    errors.push(`${field.name || field.id} is required`);
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            // Check email fields
            form.querySelectorAll('[type="email"]').forEach(field => {
                if (field.value && !Utils.isValidEmail(field.value)) {
                    isValid = false;
                    errors.push('Invalid email address');
                    field.classList.add('error');
                }
            });

            if (!isValid) {
                Toast.error(errors.join('<br>'));
            }

            return isValid;
        },

        init() {
            document.querySelectorAll('form[data-validate]').forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!this.validate(form)) {
                        e.preventDefault();
                    }
                });
            });
        }
    };

    // ==================== Mobile Menu ====================
    
    const MobileMenu = {
        init() {
            const toggle = document.querySelector('.navbar-toggle');
            const menu = document.querySelector('.navbar-menu');
            const sidebar = document.querySelector('.sidebar');

            if (toggle && menu) {
                toggle.addEventListener('click', () => {
                    menu.classList.toggle('active');
                    const icon = toggle.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('fa-bars');
                        icon.classList.toggle('fa-times');
                    }
                });
            }

            // Sidebar toggle for mobile
            const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
            if (sidebarToggle && sidebar) {
                sidebarToggle.addEventListener('click', () => {
                    sidebar.classList.toggle('active');
                });
            }
        }
    };

    // ==================== Live Preview ====================
    
    const LivePreview = {
        init() {
            const inputs = document.querySelectorAll('[data-preview]');
            
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    const target = document.querySelector(input.dataset.preview);
                    if (target) {
                        target.textContent = input.value || '-';
                    }
                });
            });
        }
    };

    // ==================== File Upload Preview ====================
    
    const FileUpload = {
        preview(input, targetId) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                const target = document.getElementById(targetId);
                
                reader.onload = function(e) {
                    if (target) {
                        if (target.tagName === 'IMG') {
                            target.src = e.target.result;
                        } else {
                            target.style.backgroundImage = `url(${e.target.result})`;
                            target.classList.add('has-image');
                        }
                    }
                };
                
                reader.readAsDataURL(input.files[0]);
            }
        },

        init() {
            document.querySelectorAll('[data-file-upload]').forEach(input => {
                input.addEventListener('change', () => {
                    const targetId = input.dataset.fileUpload;
                    this.preview(input, targetId);
                });
            });
        }
    };

    // ==================== Loading States ====================
    
    const Loading = {
        show(button) {
            if (button) {
                button.dataset.originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            }
        },

        hide(button) {
            if (button && button.dataset.originalText) {
                button.disabled = false;
                button.innerHTML = button.dataset.originalText;
            }
        }
    };

    // ==================== Search & Filter ====================
    
    const SearchFilter = {
        init() {
            const searchInputs = document.querySelectorAll('[data-search]');
            
            searchInputs.forEach(input => {
                input.addEventListener('input', Utils.debounce((e) => {
                    const query = e.target.value.toLowerCase();
                    const target = document.querySelector(e.target.dataset.search);
                    
                    if (target) {
                        const items = target.querySelectorAll('[data-search-item]');
                        items.forEach(item => {
                            const text = item.textContent.toLowerCase();
                            item.style.display = text.includes(query) ? '' : 'none';
                        });
                    }
                }, 300));
            });
        }
    };

    // ==================== Copy to Clipboard ====================
    
    const CopyToClipboard = {
        copy(text, successMessage = 'Copied to clipboard!') {
            navigator.clipboard.writeText(text).then(() => {
                Toast.success(successMessage);
            }).catch(() => {
                Toast.error('Failed to copy');
            });
        },

        init() {
            document.querySelectorAll('[data-copy]').forEach(button => {
                button.addEventListener('click', () => {
                    const text = button.dataset.copy;
                    this.copy(text);
                });
            });
        }
    };

    // ==================== Initialize Everything ====================
    
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize all modules
        ThemeManager.init();
        Modal.init();
        InvoiceCalculator.init();
        InvoiceRows.init();
        FormValidator.init();
        MobileMenu.init();
        LivePreview.init();
        FileUpload.init();
        SearchFilter.init();
        CopyToClipboard.init();

        // Global theme toggle
        document.querySelectorAll('[data-theme-toggle]').forEach(toggle => {
            toggle.addEventListener('click', () => ThemeManager.toggle());
        });

        // Delete confirmation
        document.querySelectorAll('[data-confirm]').forEach(element => {
            element.addEventListener('click', (e) => {
                const message = element.dataset.confirm || 'Are you sure?';
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });

        // Auto-dismiss alerts
        document.querySelectorAll('.alert[data-auto-dismiss]').forEach(alert => {
            setTimeout(() => {
                alert.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        });

        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    });

    // ==================== Export to Global ====================
    
    window.InvoiceHubNet = {
        Utils,
        ThemeManager,
        Toast,
        Modal,
        InvoiceCalculator,
        InvoiceRows,
        FormValidator,
        Loading,
        CopyToClipboard
    };

})();