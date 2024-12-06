const links = document.querySelectorAll('nav ul li a');
for (const link of links) {
    link.addEventListener('click', async function(e) {
        e.preventDefault();
        const targetId = this.getAttribute("href");
        const targetElement = document.querySelector(targetId);
        window.scrollTo({
            top: targetElement.offsetTop - 100,
            behavior: 'smooth'
        });
    });
}

const sections = document.querySelectorAll('.section');
const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        } else {
            entry.target.classList.remove('visible');
        }
    });
}, { threshold: 0.1 });

sections.forEach(section => {
    observer.observe(section);
});

const scrollTopBtn = document.getElementById('scrollTopBtn');

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 200) {
        scrollTopBtn.classList.add('visible');
    } else {
        scrollTopBtn.classList.remove('visible');
    }
});

async function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

const modal = document.getElementById('loginModal');
const chatButton = document.getElementById('chatButton');
const loginButton = document.getElementById('loginButton');
const closeModal = document.getElementById('closeModal');
const errorElement = document.getElementById('error');


chatButton.addEventListener('click', async function() {
    try {
        const response = await fetch('/chat', { method: 'GET' });

        if (response.status === 401) {
            modal.style.display = 'flex';
        } else if (response.ok) {

            window.location.href = '/chat';

            console.error('Произошла ошибка:', response.statusText);
        }
    } catch (error) {
        console.error('Ошибка при запросе к серверу:', error);
    }
});



loginButton.addEventListener('click', async function() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {

        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {

            modal.style.display = 'none';

            window.location.href = '/chat';
        } else {

            errorElement.textContent = data.error;
        }
    } catch (error) {
        console.error('Ошибка при входе в систему:', error);
    }
});



closeModal.onclick = function() {
    modal.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

const languageToggle = document.getElementById('languageToggle');
const chatText = document.getElementById('chatText');
const aboutTitle = document.getElementById('aboutTitle');
const aboutText = document.getElementById('aboutText');
const pricingTitle = document.getElementById('pricingTitle');
const pricingText = document.getElementById('pricingText');
const supportTitle = document.getElementById('supportTitle');
const supportText = document.getElementById('supportText');
const galleryTitle = document.getElementById('galleryTitle');
const galleryText = document.getElementById('galleryText');
const pageTitle = document.getElementById('pageTitle');
const footerText = document.getElementById('footerText');

const aboutLink = document.getElementById('aboutLink');
const pricingLink = document.getElementById('pricingLink');
const supportLink = document.getElementById('supportLink');
const galleryLink = document.getElementById('galleryLink');

let currentLanguage = 'ru';
languageToggle.addEventListener('click', async () => {
    if (currentLanguage === 'ru') {
        aboutLink.textContent = 'About Us';
        pricingLink.textContent = 'Pricing';
        supportLink.textContent = 'Support';
        galleryLink.textContent = 'Gallery';

        chatText.textContent = 'Start Chat';
        aboutTitle.textContent = 'About Us';
        aboutText.textContent = 'Learn more about our AI and how it can assist you.';
        pricingTitle.textContent = 'Pricing';
        pricingText.textContent = 'Explore our affordable pricing plans.';
        supportTitle.textContent = 'Support';
        supportText.textContent = 'Need help? Contact our 24/7 support team.';
        galleryTitle.textContent = 'Gallery';
        galleryText.textContent = 'See how our AI helps users with various tasks.';
        pageTitle.textContent = 'AI Chat';
        footerText.textContent = '&copy; 2024 AI Chat. All rights reserved.';
        languageToggle.textContent = 'Русский';
        currentLanguage = 'en';
    } else {
        aboutLink.textContent = 'О нас';
        pricingLink.textContent = 'Цены';
        supportLink.textContent = 'Поддержка';
        galleryLink.textContent = 'Галерея';

        chatText.textContent = 'Начать чат';
        aboutTitle.textContent = 'О нас';
        aboutText.textContent = 'Узнайте больше о нашем ИИ и как он может вам помочь.';
        pricingTitle.textContent = 'Цены';
        pricingText.textContent = 'Ознакомьтесь с нашими доступными тарифами.';
        supportTitle.textContent = 'Поддержка';
        supportText.textContent = 'Нужна помощь? Свяжитесь с нашей поддержкой 24/7.';
        galleryTitle.textContent = 'Галерея';
        galleryText.textContent = 'Посмотрите, как наш ИИ помогает пользователям.';
        pageTitle.textContent = 'AI Chat';
        footerText.textContent = '&copy; 2024 AI Chat. Все права защищены.';
        languageToggle.textContent = 'English';
        currentLanguage = 'ru';
    }
});

const themeToggle = document.getElementById('themeToggle');
let darkMode = false;

themeToggle.addEventListener('click', async () => {
    document.body.classList.toggle('dark-theme');
    darkMode = !darkMode;
    themeToggle.textContent = darkMode ? 'Светлая тема' : 'Тёмная тема';
});