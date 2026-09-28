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
    
    const isTrainerPage = window.location.pathname.includes('/trainers/');
    if (!isTrainerPage) return; 

    const isMobile = window.innerWidth <= 600;

    const homeBtn = document.createElement('a');
    homeBtn.innerHTML = isMobile ? "🏠" : "🏠 Меню";
    homeBtn.href = "/math-6-grade/"; 
    
    Object.assign(homeBtn.style, {
        position: 'fixed',
        top: '15px',
        left: '15px',
        padding: isMobile ? '0' : '10px 15px',
        width: isMobile ? '45px' : 'auto',
        height: isMobile ? '45px' : 'auto',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(5px)',
        color: '#333',
        textDecoration: 'none',
        borderRadius: '30px',
        boxShadow: '0 4px 10px rgba(0,0,0,0.15)',
        fontFamily: 'Segoe UI, sans-serif',
        fontWeight: 'bold',
        fontSize: isMobile ? '20px' : '14px',
        zIndex: '9999',
        border: '1px solid rgba(238, 238, 238, 0.5)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxSizing: 'border-box'
    });

    document.body.appendChild(homeBtn);

    let fadeTimeout;
    // На смартфонах убираем паузу (150мс для защиты от спама событий скролла), на ПК оставляем 2.5 секунды
    const delayBeforeFade = isMobile ? 150 : 2500;

    function wakeUp() {
        homeBtn.style.transition = 'opacity 0.2s ease, transform 0.2s ease, background-color 0.2s ease';
        homeBtn.style.opacity = '1';
        homeBtn.style.transform = 'scale(1)';
        
        clearTimeout(fadeTimeout);
        
        fadeTimeout = setTimeout(() => {
            homeBtn.style.transition = 'opacity 1.5s ease-in-out, transform 1.5s ease-in-out';
            homeBtn.style.opacity = '0.12'; 
            homeBtn.style.transform = 'scale(0.9)'; 
        }, delayBeforeFade);
    }

    homeBtn.onmouseenter = () => {
        clearTimeout(fadeTimeout);
        homeBtn.style.transition = 'all 0.2s ease';
        homeBtn.style.transform = 'scale(1.05)';
        homeBtn.style.backgroundColor = '#ffffff';
        homeBtn.style.opacity = '1';
    };
    
    homeBtn.onmouseleave = () => {
        homeBtn.style.transform = 'scale(1)';
        homeBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.85)';
        wakeUp(); 
    };

    window.addEventListener('scroll', wakeUp, { passive: true });
    window.addEventListener('mousemove', wakeUp, { passive: true });
    window.addEventListener('touchstart', wakeUp, { passive: true });
    window.addEventListener('touchend', wakeUp, { passive: true });

    wakeUp();
});
// --- КОНЕЦ КОДА КНОПКИ ---