const header = document.querySelector('.site-header');
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');
const themeToggle = document.querySelector('.theme-toggle');
const themeToggleText = document.querySelector('.theme-toggle-text');
const revealItems = document.querySelectorAll('.reveal');
const counters = document.querySelectorAll('[data-count]');
const authForms = document.querySelectorAll('[data-auth-form]');

const getDefaultTheme = () => {
  const hour = new Date().getHours();
  return hour >= 6 && hour < 18 ? 'light' : 'dark';
};

const setTheme = (theme) => {
  const isLight = theme === 'light';

  document.body.classList.toggle('light-theme', isLight);
  document.body.classList.toggle('dark-theme', !isLight);

  if (themeToggle) {
    themeToggle.setAttribute('aria-pressed', String(isLight));
  }

  if (themeToggleText) {
    themeToggleText.textContent = isLight ? 'Light' : 'Dark';
  }
};

const savedTheme = localStorage.getItem('theme');
setTheme(savedTheme || getDefaultTheme());

const setHeaderState = () => {
  if (!header) return;

  header.classList.toggle('is-scrolled', window.scrollY > 18);
};

if (header && navToggle) {
  navToggle.addEventListener('click', () => {
    const isOpen = header.classList.toggle('menu-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });
}

if (header && navMenu) {
  navMenu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      header.classList.remove('menu-open');
      navToggle?.setAttribute('aria-expanded', 'false');
    });
  });
}

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const nextTheme = document.body.classList.contains('light-theme') ? 'dark' : 'light';

    localStorage.setItem('theme', nextTheme);
    setTheme(nextTheme);
  });
}

if (revealItems.length > 0) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;

      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0.18
  });

  revealItems.forEach((item, index) => {
    item.style.transitionDelay = `${Math.min(index * 70, 280)}ms`;
    revealObserver.observe(item);
  });
}

const animateCounter = (element) => {
  const target = Number(element.dataset.count || 0);
  const suffix = element.dataset.suffix || '+';
  const duration = 1200;
  const startTime = performance.now();

  const updateValue = (currentTime) => {
    const progress = Math.min((currentTime - startTime) / duration, 1);
    const value = Math.floor(progress * target);
    element.textContent = `${value}${suffix}`;

    if (progress < 1) {
      requestAnimationFrame(updateValue);
    } else {
      element.textContent = `${target}${suffix}`;
    }
  };

  requestAnimationFrame(updateValue);
};

if (counters.length > 0) {
  const counterObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;

      animateCounter(entry.target);
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0.7
  });

  counters.forEach((counter) => {
    counterObserver.observe(counter);
  });
}

const renderAuthFeedback = (form, category, message) => {
  const feedback = form.parentElement.querySelector('.auth-feedback');

  if (!feedback) return;

  feedback.innerHTML = '';

  if (!message) return;

  const banner = document.createElement('div');
  banner.className = `flash-banner flash-${category || 'error'}`;
  banner.textContent = message;
  feedback.appendChild(banner);
};

if (authForms.length > 0) {
  authForms.forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      const submitButton = form.querySelector('button[type="submit"]');
      const formData = new FormData(form);

      renderAuthFeedback(form, '', '');

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.dataset.originalText = submitButton.textContent;
        submitButton.textContent = 'Please wait...';
      }

      try {
        const response = await fetch(form.action || window.location.href, {
          method: form.method || 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
          },
        });

        const payload = await response.json();
        renderAuthFeedback(form, payload.category, payload.message);

        if (payload.ok && payload.redirect_url) {
          window.location.href = payload.redirect_url;
        }
      } catch (error) {
        renderAuthFeedback(form, 'error', 'Something went wrong. Please try again.');
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = submitButton.dataset.originalText || 'Submit';
        }
      }
    });
  });
}

window.addEventListener('scroll', setHeaderState, { passive: true });
window.addEventListener('load', setHeaderState);
setHeaderState();
