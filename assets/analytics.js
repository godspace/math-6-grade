// Файл: assets/analytics.js

(function(m,e,t,r,i,k,a){
    m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();
    for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
    k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
})(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=106746549', 'ym');

ym(106746549, 'init', {
    ssr: true,
    webvisor: true,
    clickmap: true,
    ecommerce: "dataLayer",
    referrer: document.referrer,
    url: location.href,
    accurateTrackBounce: true,
    trackLinks: true
});

// --- НАЧАЛО КОДА КНОПКИ "ДОМОЙ" ---
document.addEventListener("DOMContentLoaded", function() {
    
    // Надежная проверка: кнопка нужна ТОЛЬКО если мы находимся внутри папки тренажеров
    const isTrainerPage = window.location.pathname.includes('/trainers/');
    
    // Если это не тренажер (значит это главная страница) — просто выходим
    if (!isTrainerPage) return; 

    // Создаем кнопку
    const homeBtn = document.createElement('a');
    homeBtn.innerHTML = "🏠 Меню";
    
    // Ссылка ведет в корень репозитория
    homeBtn.href = "/math-6-grade/"; 
    
    // Добавляем стили
    Object.assign(homeBtn.style, {
        position: 'fixed',
        top: '20px',
        left: '20px',
        padding: '10px 15px',
        backgroundColor: '#ffffff',
        color: '#333',
        textDecoration: 'none',
        borderRadius: '30px',
        boxShadow: '0 4px 10px rgba(0,0,0,0.15)',
        fontFamily: 'Segoe UI, sans-serif',
        fontWeight: 'bold',
        fontSize: '14px',
        zIndex: '9999',
        border: '1px solid #eee',
        transition: 'transform 0.2s',
        cursor: 'pointer'
    });

    // Эффекты при наведении
    homeBtn.onmouseenter = () => {
        homeBtn.style.transform = 'scale(1.05)';
        homeBtn.style.backgroundColor = '#f8f9fa';
        homeBtn.style.boxShadow = '0 6px 15px rgba(0,0,0,0.2)';
    };
    homeBtn.onmouseleave = () => {
        homeBtn.style.transform = 'scale(1)';
        homeBtn.style.backgroundColor = '#ffffff';
        homeBtn.style.boxShadow = '0 4px 10px rgba(0,0,0,0.15)';
    };

    // Вставляем кнопку в тело страницы
    document.body.appendChild(homeBtn);
});
// --- КОНЕЦ КОДА КНОПКИ ---