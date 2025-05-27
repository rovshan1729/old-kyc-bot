document.addEventListener('DOMContentLoaded', () => {
    const logo = document.querySelector('.logo');
    const body = document.body;

    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
    }

    logo.addEventListener('click', (e) => {
        e.preventDefault();
        body.classList.toggle('dark-mode');
        const isDark = body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');

    const toggleMenu = (e) => {
        e.preventDefault();
        e.stopPropagation();
        navMenu.classList.toggle('active');
        menuToggle.classList.toggle('active');
    };

    menuToggle.addEventListener('click', toggleMenu);
    menuToggle.addEventListener('touchstart', toggleMenu);

    document.addEventListener('click', (e) => {
        if (!navMenu.contains(e.target) && 
            !menuToggle.contains(e.target) && 
            navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            menuToggle.classList.remove('active');
        }
    });

    document.addEventListener('touchstart', (e) => {
        if (!navMenu.contains(e.target) && 
            !menuToggle.contains(e.target) && 
            navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            menuToggle.classList.remove('active');
        }
    });

    const datetime = document.getElementById('datetime');
    const updateDateTime = () => {
        const now = new Date();
        const options = {
            weekday: 'short',
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'UTC'
        };
        datetime.textContent = `${now.toLocaleString('en-US', options)} UTC`;
    };
    updateDateTime();
    setInterval(updateDateTime, 60000);
});