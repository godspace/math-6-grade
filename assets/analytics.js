// Файл: assets/analytics.js

// --- Яндекс Метрика ---
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

// --- Стили для плавного смещения кнопок при появлении/закрытии баннера ---
const style = document.createElement('style');
style.innerHTML = `
    #google_translate_element { display: none !important; }
    
    body { 
        position: relative !important; 
        transition: top 0.3s ease !important;
    }

    .floating-ui-element {
        transition: transform 0.3s ease, opacity 0.3s ease;
        transform: translateY(0px); /* По умолчанию на месте */
    }

    /* Когда Гугл сдвигает body вниз, кнопки тоже едут за ним */
    body.goog-banner-active .floating-ui-element {
        transform: translateY(var(--banner-offset, 40px));
    }
`;
document.head.appendChild(style);

// --- Глобальная функция инициализации ---
window.googleTranslateElementInit = function() {
    new google.translate.TranslateElement({
        pageLanguage: 'ru',
        autoDisplay: false
    }, 'google_translate_element');
};

document.addEventListener("DOMContentLoaded", function() {
    const isTrainerPage = window.location.pathname.includes('/trainers/');
    const isMobile = window.innerWidth <= 600;
    
    // 1. Создаем скрытый контейнер для движка Google
    const hiddenTranslateDiv = document.createElement('div');
    hiddenTranslateDiv.id = 'google_translate_element';
    document.body.appendChild(hiddenTranslateDiv);

    const gtScript = document.createElement('script');
    gtScript.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    document.body.appendChild(gtScript);

    // 2. Создаем нашу панель языков (EN, ES, ZH)
    const langPanel = document.createElement('div');
    langPanel.className = 'floating-ui-element';
    langPanel.style.cssText = 'position:fixed; top:15px; right:15px; z-index:9999; display:flex; gap:8px; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(5px); padding: 8px 12px; border-radius: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid rgba(238, 238, 238, 0.5); font-family: "Segoe UI", sans-serif; align-items: center;';
    
    const languages = [
        { code: 'en', text: 'EN' },
        { code: 'es', text: 'ES' },
        { code: 'zh-CN', text: 'ZH' }
    ];

    languages.forEach(lang => {
        const btn = document.createElement('button');
        btn.innerText = lang.text;
        btn.style.cssText = 'background: transparent; border: none; cursor: pointer; font-weight: bold; color: #333; font-size: 14px; padding: 4px 8px; border-radius: 15px; transition: 0.2s;';
        
        btn.onmouseenter = () => btn.style.backgroundColor = 'rgba(0,0,0,0.1)';
        btn.onmouseleave = () => btn.style.backgroundColor = 'transparent';
        
        btn.onclick = () => {
            const selectField = document.querySelector(".goog-te-combo");
            if (selectField) {
                selectField.value = lang.code;
                selectField.dispatchEvent(new Event('change'));
            }
        };
        langPanel.appendChild(btn);
    });

    document.body.appendChild(langPanel);

    // 3. Отслеживаем появление и закрытие баннера Google Translate через MutationObserver
    const observer = new MutationObserver(() => {
        const bodyTop = parseInt(document.body.style.top, 10);
        if (bodyTop && bodyTop > 0) {
            document.body.classList.add('goog-banner-active');
            // Динамически подстраиваем сдвиг под реальную высоту баннера Гугла
            document.documentElement.style.setProperty('--banner-offset', bodyTop + 'px');
        } else {
            document.body.classList.remove('goog-banner-active');
        }
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['style'] });

    // 4. Логика для страниц тренажеров (Кнопка Меню и совместное затухание)
    if (isTrainerPage) {
        const homeBtn = document.createElement('a');
        homeBtn.className = 'floating-ui-element';
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
        const delayBeforeFade = isMobile ? 150 : 2500;

        function wakeUp() {
            homeBtn.style.transition = 'opacity 0.2s ease, transform 0.2s ease, background-color 0.2s ease';
            homeBtn.style.opacity = '1';
            
            langPanel.style.transition = 'opacity 0.2s ease';
            langPanel.style.opacity = '1';
            
            clearTimeout(fadeTimeout);
            
            fadeTimeout = setTimeout(() => {
                homeBtn.style.transition = 'opacity 1.5s ease-in-out';
                homeBtn.style.opacity = '0.12'; 
                
                langPanel.style.transition = 'opacity 1.5s ease-in-out';
                langPanel.style.opacity = '0.12';
            }, delayBeforeFade);
        }

        homeBtn.onmouseenter = () => {
            clearTimeout(fadeTimeout);
            homeBtn.style.transition = 'all 0.2s ease';
            homeBtn.style.backgroundColor = '#ffffff';
            homeBtn.style.opacity = '1';
            langPanel.style.opacity = '1'; 
        };
        
        homeBtn.onmouseleave = () => {
            homeBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.85)';
            wakeUp(); 
        };

        langPanel.onmouseenter = () => {
            clearTimeout(fadeTimeout);
            langPanel.style.opacity = '1';
            homeBtn.style.opacity = '1'; 
        };
        
        langPanel.onmouseleave = () => {
            wakeUp();
        };

        window.addEventListener('scroll', wakeUp, { passive: true });
        window.addEventListener('mousemove', wakeUp, { passive: true });
        window.addEventListener('touchstart', wakeUp, { passive: true });
        window.addEventListener('touchend', wakeUp, { passive: true });

        wakeUp();
    }
});