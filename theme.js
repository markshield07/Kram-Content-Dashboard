// Theme definitions
const themes = {
    dark: {
        '--bg-primary': '#0d0d0d',
        '--bg-secondary': '#1a1a1a',
        '--bg-card': '#141414',
        '--text-primary': '#ffffff',
        '--text-secondary': '#a0a0a0',
        '--accent': '#f7931a',
        '--accent-hover': '#ffa726',
        '--border': '#2a2a2a',
        '--success': '#34c759',
        '--error': '#ff3b30'
    },
    light: {
        '--bg-primary': '#f5f5f7',
        '--bg-secondary': '#ffffff',
        '--bg-card': '#ffffff',
        '--text-primary': '#1d1d1f',
        '--text-secondary': '#6e6e73',
        '--accent': '#f7931a',
        '--accent-hover': '#e8850f',
        '--border': '#d2d2d7',
        '--success': '#34c759',
        '--error': '#ff3b30'
    }
};

// SVG icons for the toggle button
const sunIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';

const moonIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';

/**
 * Apply a theme by setting all CSS custom properties on :root.
 * Persists the choice to localStorage and updates the toggle button icon.
 *
 * @param {string} theme - Either 'dark' or 'light'
 */
function applyTheme(theme) {
    const root = document.documentElement;
    const vars = themes[theme];

    if (!vars) return;

    Object.entries(vars).forEach(([key, value]) => {
        root.style.setProperty(key, value);
    });

    localStorage.setItem('contentai-theme', theme);

    // Update toggle button icon: show sun when in dark mode (click to go light),
    // show moon when in light mode (click to go dark)
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.innerHTML = theme === 'dark' ? sunIcon : moonIcon;
        btn.title = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';
    }
}

/**
 * Toggle between dark and light themes.
 */
function toggleTheme() {
    const current = localStorage.getItem('contentai-theme') || 'dark';
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

// Execute immediately to prevent flash of unstyled/wrong-theme content.
// This runs synchronously before the browser paints, as long as the script
// is included in <head> without defer/async.
(function() {
    const theme = localStorage.getItem('contentai-theme') || 'dark';
    applyTheme(theme);
})();
