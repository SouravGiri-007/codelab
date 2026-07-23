// CodeLab — Main JavaScript

document.addEventListener('DOMContentLoaded', () => {

    /* ─── Hamburger Menu Toggle ──────────────────────────────── */
    const hamburger = document.getElementById('hamburgerBtn');
    const navLinks = document.getElementById('navLinks');
    const navOverlay = document.getElementById('navOverlay');

    if (hamburger && navLinks && navOverlay) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('mobile-open');
            navOverlay.classList.toggle('show');
            document.body.classList.toggle('nav-open');
        });

        navOverlay.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navLinks.classList.remove('mobile-open');
            navOverlay.classList.remove('show');
            document.body.classList.remove('nav-open');
        });

        // Close nav when a link is clicked
        navLinks.querySelectorAll('.nav-link, .nav-btn').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navLinks.classList.remove('mobile-open');
                navOverlay.classList.remove('show');
                document.body.classList.remove('nav-open');
            });
        });
    }

    /* ─── Mobile Sidebar Toggle Helper ──────────────────────── */
    function setupMobileSidebar(toggleId, sidebarSelector) {
        const toggle = document.getElementById(toggleId);
        const sidebar = document.querySelector(sidebarSelector);
        if (!toggle || !sidebar) return;

        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
            toggle.classList.toggle('active');

            let backdrop = document.querySelector('.sidebar-backdrop');
            if (sidebar.classList.contains('mobile-open')) {
                if (!backdrop) {
                    backdrop = document.createElement('div');
                    backdrop.className = 'sidebar-backdrop';
                    document.body.appendChild(backdrop);
                    backdrop.addEventListener('click', () => {
                        sidebar.classList.remove('mobile-open');
                        toggle.classList.remove('active');
                        backdrop.remove();
                    });
                }
            } else {
                if (backdrop) backdrop.remove();
            }
        });
    }

    // Setup Explore sidebar toggle
    setupMobileSidebar('filterToggle', '.explore-sidebar');

    // Setup News sidebar toggle
    setupMobileSidebar('newsSidebarToggle', '.news-sidebar');

    /* ─── Dropdown menu toggle (for mobile/touch) ────────────── */
    const dropdownBtn = document.querySelector('.nav-avatar');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    if (dropdownBtn && dropdownMenu) {
        dropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
        document.addEventListener('click', () => {
            dropdownMenu.classList.remove('show');
        });
    }

    /* ─── Auto-dismiss flash messages after 5s ───────────────── */
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            flash.style.transition = 'all 0.3s ease';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });

    /* ─── Keyboard shortcut: Ctrl+K to focus search ──────────── */
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input');
            if (searchInput) searchInput.focus();
        }
    });

    /* ─── Fix iOS 100vh issue (mobile address bar) ───────────── */
    const setVh = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
    setVh();
    window.addEventListener('resize', setVh);

    /* ─── Touch-friendly: prevent 300ms tap delay ────────────── */
    if ('ontouchstart' in window) {
        document.querySelectorAll('a, button, .news-card, .snippet-card').forEach(el => {
            el.style.touchAction = 'manipulation';
        });
    }
});
