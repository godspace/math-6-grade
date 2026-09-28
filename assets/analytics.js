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
    
    // Проверка: кнопка нужна ТОЛЬКО внутри папки тренажеров
    const isTrainerPage = window.location.pathname.includes('/trainers/');
    if (!isTrainerPage) return; 

    // Определяем мобильное устройство
    const isMobile = window.innerWidth <= 600;

    const homeBtn = document.createElement('a');
    // На смартфонах оставляем только эмодзи домика
    homeBtn.innerHTML = isMobile ? "🏠" : "🏠 Меню";
    homeBtn.href = "/math-6-grade/"; 
    
    // Стили кнопки
    Object.assign(homeBtn.style, {
        position: 'fixed',
        top: '20px',
        left: '20px',
        padding: isMobile ? '10px 12px' : '10px 15px',
        backgroundColor: 'rgba(255, 255, 255, 0.85)', // Слегка прозрачный белый
        backdropFilter: 'blur(5px)', // Эффект матового стекла (iOS style)
        color: '#333',
        textDecoration: 'none',
        borderRadius: '30px',
        boxShadow: '0 4px 10px rgba(0,0,0,0.15)',
        fontFamily: 'Segoe UI, sans-serif',
        fontWeight: 'bold',
        fontSize: isMobile ? '18px' : '14px',
        zIndex: '9999',
        border: '1px solid rgba(238, 238, 238, 0.5)',
        transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)', // Плавная анимация
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: '1',
        transform: 'translateY(0)'
    });

    // Эффекты при наведении
    homeBtn.onmouseenter = () => {
        if (window.scrollY <= 50) {
            homeBtn.style.transform = 'scale(1.05)';
            homeBtn.style.backgroundColor = '#ffffff';
        }
    };
    homeBtn.onmouseleave = () => {
        if (window.scrollY <= 50) {
            homeBtn.style.transform = 'scale(1)';
            homeBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.85)';
        }
    };

    document.body.appendChild(homeBtn);

    // Логика исчезновения при прокрутке
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            // Прячем кнопку (уводим чуть вверх и делаем прозрачной)
            homeBtn.style.opacity = '0';
            homeBtn.style.pointerEvents = 'none';
            homeBtn.style.transform = 'translateY(-20px)';
        } else {
            // Показываем кнопку, если вернулись наверх
            homeBtn.style.opacity = '1';
            homeBtn.style.pointerEvents = 'auto';
            homeBtn.style.transform = 'translateY(0)';
        }
    });
});
// --- КОНЕЦ КОДА КНОПКИ ---