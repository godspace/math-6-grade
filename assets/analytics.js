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
    // 1. Проверяем, не находимся ли мы уже на главной странице
    // (чтобы кнопка не появлялась в самом меню)
    const isHomePage = window.location.pathname.endsWith('/math-6-grade/') || 
                       window.location.pathname.endsWith('/index.html') ||
                       window.location.pathname === '/';
    
    // Если это главная - ничего не делаем
    if (isHomePage && document.title.includes("Меню")) return; 

    // 2. Создаем кнопку
    const homeBtn = document.createElement('a');
    homeBtn.innerHTML = "🏠 Меню";
    
    // ВАЖНО: Ссылка ведет в корень репозитория
    homeBtn.href = "/math-6-grade/"; 
    
    // 3. Добавляем стили прямо через JS (чтобы не лезть в CSS файлы)
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
        zIndex: '9999', // Чтобы была поверх всего
        border: '1px solid #eee',
        transition: 'transform 0.2s',
        cursor: 'pointer'
    });

    // 4. Эффект при наведении
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

    // 5. Вставляем кнопку в тело страницы
    document.body.appendChild(homeBtn);
});
// --- КОНЕЦ КОДА КНОПКИ ---