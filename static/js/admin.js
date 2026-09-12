/**
 * DevRise Admin Dashboard - JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize user menu
  const userBtn = document.querySelector('.admin-user-btn');
  const userDropdown = document.querySelector('.admin-user-dropdown');
  
  if (userBtn && userDropdown) {
    userBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      const isOpen = userBtn.getAttribute('aria-expanded') === 'true';
      userBtn.setAttribute('aria-expanded', !isOpen);
      userDropdown.style.display = isOpen ? 'none' : 'block';
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
      if (!userBtn.contains(e.target) && !userDropdown.contains(e.target)) {
        userBtn.setAttribute('aria-expanded', 'false');
        userDropdown.style.display = 'none';
      }
    });
  }

  // Sidebar toggle for mobile
  const sidebarToggle = document.querySelector('.sidebar-toggle-btn');
  const sidebarClose = document.querySelector('.sidebar-close-btn');
  const sidebar = document.querySelector('.admin-sidebar');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      sidebar.classList.toggle('is-open');
      const isOpen = sidebar.classList.contains('is-open');
      sidebarToggle.setAttribute('aria-expanded', isOpen);
    });
  }

  if (sidebarClose) {
    sidebarClose.addEventListener('click', function() {
      sidebar.classList.remove('is-open');
      if (sidebarToggle) {
        sidebarToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Close sidebar when navigating on mobile
  const navLinks = document.querySelectorAll('.admin-nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('is-open');
        if (sidebarToggle) {
          sidebarToggle.setAttribute('aria-expanded', 'false');
        }
      }
    });
  });

  // Flash message auto-dismiss
  const flashBanners = document.querySelectorAll('.admin-flash-banner');
  flashBanners.forEach(banner => {
    const closeBtn = banner.querySelector('.admin-flash-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        banner.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
          banner.remove();
        }, 300);
      });
    }

    // Auto-dismiss after 5 seconds for success messages
    if (banner.classList.contains('admin-flash-success')) {
      setTimeout(() => {
        if (banner.parentElement) {
          banner.style.animation = 'slideOut 0.3s ease-out forwards';
          setTimeout(() => {
            banner.remove();
          }, 300);
        }
      }, 5000);
    }
  });

  // Add slide out animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideOut {
      from {
        opacity: 1;
        transform: translateX(0);
      }
      to {
        opacity: 0;
        transform: translateX(-20px);
      }
    }
  `;
  document.head.appendChild(style);
});

/**
 * Utility function to fetch admin API endpoints
 * @param {string} url - The API endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise}
 */
function adminApiCall(url, options = {}) {
  const defaultOptions = {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/json'
    }
  };

  return fetch(url, { ...defaultOptions, ...options })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    });
}

/**
 * Show a flash message programmatically
 * @param {string} message - The message to display
 * @param {string} category - Message category: 'success', 'error', 'warning', 'info'
 */
function showFlashMessage(message, category = 'info') {
  const stack = document.querySelector('.admin-flash-stack');
  if (!stack) {
    console.warn('Flash message stack not found');
    return;
  }

  const banner = document.createElement('div');
  banner.className = `admin-flash-banner admin-flash-${category}`;
  banner.setAttribute('role', 'alert');
  banner.innerHTML = `
    <span>${message}</span>
    <button type="button" class="admin-flash-close" aria-label="Close notification">&times;</button>
  `;

  stack.appendChild(banner);

  const closeBtn = banner.querySelector('.admin-flash-close');
  closeBtn.addEventListener('click', function() {
    banner.style.animation = 'slideOut 0.3s ease-out forwards';
    setTimeout(() => {
      banner.remove();
    }, 300);
  });

  if (category === 'success') {
    setTimeout(() => {
      if (banner.parentElement) {
        banner.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
          banner.remove();
        }, 300);
      }
    }, 5000);
  }
}
