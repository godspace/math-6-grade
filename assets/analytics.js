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

// --- Глобальная система наград и лутбоксов (Adv.Cake) ---
window.RewardSystem = {
    // Базовая ссылка (склеена с лендингом и токеном, ждёт только параметр sub1)
    basePartnerLink: "https://go.avred.online/e7e83cba257a28c0?erid=2VfnxyV46NP&m=1&dl=https://foxford.ru/free-lessons-group",
    
    // Юридический текст с актуальным erid из твоей ссылки
    legalText: "Реклама. ООО ФОКСФОРД, ИНН 7726464100, erid: 2VfnxyV46NP",
    
    errorsCount: 0,

    init() {
        this.injectStyles();
        this.injectHTML();
    },

    injectStyles() {
        const style = document.createElement('style');
        style.innerHTML = `
            /* Стили окна Лутбокса */
            .lootbox-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(10px);
                display: flex; justify-content: center; align-items: center;
                z-index: 10000; opacity: 0; pointer-events: none;
                transition: opacity 0.4s ease; font-family: 'Segoe UI', sans-serif;
            }
            .lootbox-overlay.active { opacity: 1; pointer-events: all; }
            
            .lootbox-modal {
                background: linear-gradient(145deg, #1e293b, #0f172a);
                border: 2px solid #f59e0b; border-radius: 24px;
                padding: 40px 30px; max-width: 420px; width: 90%; text-align: center;
                box-shadow: 0 20px 50px rgba(245, 158, 11, 0.2), inset 0 0 20px rgba(245, 158, 11, 0.05);
                transform: scale(0.5) translateY(50px);
                transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                position: relative; overflow: hidden;
            }
            .lootbox-overlay.active .lootbox-modal { transform: scale(1) translateY(0); }

            /* Анимированная эмблема (Favicon) */
            .lootbox-icon-wrapper {
                position: relative; width: 100px; height: 100px; margin: 0 auto 20px auto;
                display: flex; justify-content: center; align-items: center;
            }
            .lootbox-glow {
                position: absolute; width: 100%; height: 100%;
                background: conic-gradient(from 0deg, transparent, #f59e0b, transparent, #3b82f6, transparent);
                border-radius: 50%;
                animation: spinGlow 4s linear infinite;
                filter: blur(10px); opacity: 0.7;
            }
            .lootbox-icon {
                font-size: 4rem; position: relative; z-index: 2;
                animation: floatIcon 3s ease-in-out infinite;
                filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.8));
            }

            @keyframes spinGlow { 100% { transform: rotate(360deg); } }
            @keyframes floatIcon {
                0%, 100% { transform: translateY(0) scale(1); }
                50% { transform: translateY(-10px) scale(1.1); }
            }

            .lootbox-title { color: #f59e0b; font-size: 1.8rem; font-weight: 900; text-transform: uppercase; margin-bottom: 10px; text-shadow: 0 0 15px rgba(245, 158, 11, 0.4); }
            .lootbox-text { color: #e2e8f0; font-size: 1.05rem; line-height: 1.5; margin-bottom: 25px; }
            
            .lootbox-btn {
                display: inline-block; background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white; text-decoration: none; padding: 16px 35px; border-radius: 30px;
                font-size: 1.2rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;
                box-shadow: 0 5px 20px rgba(245, 158, 11, 0.4); transition: all 0.2s; margin-bottom: 15px;
            }
            .lootbox-btn:hover { transform: scale(1.05); box-shadow: 0 8px 25px rgba(245, 158, 11, 0.6); }
            
            .lootbox-close { background: transparent; border: none; color: #94a3b8; font-size: 0.95rem; cursor: pointer; text-decoration: underline; transition: color 0.2s; }
            .lootbox-close:hover { color: white; }
            .lootbox-legal { font-size: 0.6rem; color: #475569; margin-top: 20px; line-height: 1.2; }

            /* Стили для мягкой подсказки (Спасательный круг) */
            .soft-lifeline {
                display: none; position: fixed; bottom: 20px; right: 20px;
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95));
                border-left: 4px solid #3b82f6; border-radius: 12px; padding: 15px 20px;
                max-width: 350px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 9998;
                font-family: 'Segoe UI', sans-serif; animation: slideInRight 0.4s ease forwards;
            }
            @keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
            .soft-lifeline .title { color: white; font-weight: bold; margin-bottom: 5px; font-size: 0.95rem; }
            .soft-lifeline .text { color: #94a3b8; font-size: 0.85rem; margin-bottom: 10px; line-height: 1.4; }
            .soft-lifeline a { color: #60a5fa; text-decoration: none; font-size: 0.85rem; font-weight: bold; border: 1px solid rgba(59,130,246,0.3); padding: 5px 10px; border-radius: 15px; display: inline-block; transition: 0.2s; }
            .soft-lifeline a:hover { background: #3b82f6; color: white; }
            .soft-lifeline .close { position: absolute; top: 10px; right: 10px; background: none; border: none; color: #94a3b8; cursor: pointer; }
        `;
        document.head.appendChild(style);
    },

    injectHTML() {
        // Окно Лутбокса
        const overlay = document.createElement('div');
        overlay.className = 'lootbox-overlay';
        overlay.id = 'global-lootbox';
        overlay.innerHTML = `
            <div class="lootbox-modal">
                <div class="lootbox-icon-wrapper">
                    <div class="lootbox-glow"></div>
                    <div class="lootbox-icon">🎮</div>
                </div>
                <div class="lootbox-title">Уровень пройден!</div>
                <div class="lootbox-text" id="lootbox-message">
                    Отличная работа! Ты получаешь редкий лут: 2 бесплатных занятия с крутыми преподавателями.
                </div>
                <a href="#" target="_blank" class="lootbox-btn" id="lootbox-action-btn" rel="noopener">Забрать награду</a><br>
                <button class="lootbox-close" onclick="window.RewardSystem.closeWin()">Продолжить тренировку</button>
                <div class="lootbox-legal">${this.legalText}</div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Мягкая подсказка для ошибающихся
        const lifeline = document.createElement('div');
        lifeline.className = 'soft-lifeline';
        lifeline.id = 'global-lifeline';
        lifeline.innerHTML = `
            <button class="close" onclick="document.getElementById('global-lifeline').style.display='none'">✖</button>
            <div class="title">💡 Нужна помощь?</div>
            <div class="text">Застрял? Разбери сложную тему с преподавателем бесплатно, чтобы щёлкать такие задачи как орешки.</div>
            <a href="#" target="_blank" id="lifeline-action-btn" rel="noopener">Забрать 2 урока ➔</a>
            <div style="font-size: 0.55rem; color: #475569; margin-top: 5px;">${this.legalText}</div>
        `;
        document.body.appendChild(lifeline);
    },

    showWin(customMessage, subId = 'general') {
        if (customMessage) {
            document.getElementById('lootbox-message').innerHTML = customMessage + "<br><br>Ты получаешь редкий лут: 2 бесплатных занятия с крутыми преподавателями.";
        }
        
        // Формируем финальную динамическую ссылку с передачей ID тренажёра
        const finalLink = `${this.basePartnerLink}&sub1=${subId}`;
        document.getElementById('lootbox-action-btn').href = finalLink;
        
        document.getElementById('global-lootbox').classList.add('active');
    },

    closeWin() {
        document.getElementById('global-lootbox').classList.remove('active');
    },

    registerError(subId = 'general') {
        this.errorsCount++;
        if (this.errorsCount >= 3) {
            const finalLink = `${this.basePartnerLink}&sub1=${subId}_error_help`;
            document.getElementById('lifeline-action-btn').href = finalLink;
            document.getElementById('global-lifeline').style.display = 'block';
        }
    },

    resetErrors() {
        this.errorsCount = 0;
        const lifeline = document.getElementById('global-lifeline');
        if (lifeline) lifeline.style.display = 'none';
    }
};

// --- Стили для плавного смещения и исчезновения элементов ---
const style = document.createElement('style');
style.innerHTML = `
    #google_translate_element { display: none !important; }
    body { position: relative !important; transition: top 0.3s ease !important; }
    .floating-ui-element { transition: transform 0.3s ease, opacity 0.4s ease; transform: translateY(0px); opacity: 1; }
    body.goog-banner-active .floating-ui-element { transform: translateY(var(--banner-offset, 40px)); }
`;
document.head.appendChild(style);

window.googleTranslateElementInit = function() {
    new google.translate.TranslateElement({ pageLanguage: 'ru', autoDisplay: false }, 'google_translate_element');
};

document.addEventListener("DOMContentLoaded", function() {
    // Инициализация системы наград
    window.RewardSystem.init();

    const isTrainerPage = window.location.pathname.includes('/trainers/');
    const isMobile = window.innerWidth <= 600;
    
    // 1. Google Translate
    const hiddenTranslateDiv = document.createElement('div');
    hiddenTranslateDiv.id = 'google_translate_element';
    document.body.appendChild(hiddenTranslateDiv);

    const gtScript = document.createElement('script');
    gtScript.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    document.body.appendChild(gtScript);

    // 2. Языковая панель
    const langPanel = document.createElement('div');
    langPanel.className = 'floating-ui-element';
    langPanel.style.cssText = 'position:fixed; top:15px; right:15px; z-index:9999; display:flex; gap:8px; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(5px); padding: 8px 12px; border-radius: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid rgba(238, 238, 238, 0.5); font-family: "Segoe UI", sans-serif; align-items: center;';
    
    const languages = [ { code: 'en', text: 'EN' }, { code: 'es', text: 'ES' }, { code: 'zh-CN', text: 'ZH' } ];
    languages.forEach(lang => {
        const btn = document.createElement('button');
        btn.innerText = lang.text;
        btn.style.cssText = 'background: transparent; border: none; cursor: pointer; font-weight: bold; color: #333; font-size: 14px; padding: 4px 8px; border-radius: 15px; transition: 0.2s;';
        btn.onmouseenter = () => btn.style.backgroundColor = 'rgba(0,0,0,0.1)';
        btn.onmouseleave = () => btn.style.backgroundColor = 'transparent';
        btn.onclick = () => {
            const selectField = document.querySelector(".goog-te-combo");
            if (selectField) { selectField.value = lang.code; selectField.dispatchEvent(new Event('change')); }
        };
        langPanel.appendChild(btn);
    });
    document.body.appendChild(langPanel);

    // 3. Отслеживание Google Translate
    const observer = new MutationObserver(() => {
        const bodyTop = parseInt(document.body.style.top, 10);
        if (bodyTop && bodyTop > 0) {
            document.body.classList.add('goog-banner-active');
            document.documentElement.style.setProperty('--banner-offset', bodyTop + 'px');
        } else {
            document.body.classList.remove('goog-banner-active');
        }
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['style'] });

    // 4. Кнопка Меню
    let homeBtn = null;
    if (isTrainerPage) {
        homeBtn = document.createElement('a');
        homeBtn.className = 'floating-ui-element';
        homeBtn.innerHTML = isMobile ? "🏠" : "🏠 Меню";
        homeBtn.href = "/math-6-grade/"; 
        Object.assign(homeBtn.style, {
            position: 'fixed', top: '15px', left: '15px', padding: isMobile ? '0' : '10px 15px',
            width: isMobile ? '45px' : 'auto', height: isMobile ? '45px' : 'auto',
            backgroundColor: 'rgba(255, 255, 255, 0.85)', backdropFilter: 'blur(5px)', color: '#333',
            textDecoration: 'none', borderRadius: '30px', boxShadow: '0 4px 10px rgba(0,0,0,0.15)',
            fontFamily: 'Segoe UI, sans-serif', fontWeight: 'bold', fontSize: isMobile ? '20px' : '14px',
            zIndex: '9999', border: '1px solid rgba(238, 238, 238, 0.5)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box'
        });
        document.body.appendChild(homeBtn);
    }

    // 5. Умное скрытие
    let fadeTimeout;
    function showElements() {
        if (window.scrollY < 50) {
            if (homeBtn) { homeBtn.style.opacity = '1'; homeBtn.style.pointerEvents = 'auto'; }
            langPanel.style.opacity = '1'; langPanel.style.pointerEvents = 'auto';
            clearTimeout(fadeTimeout);
            fadeTimeout = setTimeout(() => {
                if (homeBtn) homeBtn.style.opacity = '0.12';
                langPanel.style.opacity = '0.12';
            }, 1000);
        }
    }
    function hideElements() {
        if (window.scrollY >= 50) {
            clearTimeout(fadeTimeout);
            if (homeBtn) { homeBtn.style.opacity = '0'; homeBtn.style.pointerEvents = 'none'; }
            langPanel.style.opacity = '0'; langPanel.style.pointerEvents = 'none';
        }
    }

    if (homeBtn) {
        homeBtn.onmouseenter = () => { if (window.scrollY < 50) { clearTimeout(fadeTimeout); homeBtn.style.opacity = '1'; homeBtn.style.backgroundColor = '#ffffff'; langPanel.style.opacity = '1'; } };
        homeBtn.onmouseleave = () => { homeBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.85)'; showElements(); };
    }
    langPanel.onmouseenter = () => { if (window.scrollY < 50) { clearTimeout(fadeTimeout); langPanel.style.opacity = '1'; if (homeBtn) homeBtn.style.opacity = '1'; } };
    langPanel.onmouseleave = () => { showElements(); };

    window.addEventListener('scroll', () => { if (window.scrollY >= 50) hideElements(); else showElements(); }, { passive: true });
    window.addEventListener('mousemove', showElements, { passive: true });
    window.addEventListener('touchstart', showElements, { passive: true });
    window.addEventListener('touchend', showElements, { passive: true });
    showElements();

    // 6. Cookie-баннер
    if (!localStorage.getItem('cookieConsentAccepted')) {
        const cookieBanner = document.createElement('div');
        cookieBanner.style.cssText = 'position:fixed; bottom:0; left:0; width:100%; background:rgba(30, 30, 30, 0.95); color:#fff; padding:15px 20px; box-sizing:border-box; z-index:10000; display:flex; justify-content:space-between; align-items:center; font-family:"Segoe UI", sans-serif; font-size:14px; backdrop-filter:blur(5px); flex-wrap:wrap; gap:10px; transition: opacity 0.3s ease;';
        cookieBanner.innerHTML = `
            <div style="flex: 1; min-width: 250px;">Мы используем файлы cookie (в том числе Яндекс.Метрику) для анализа статистики и улучшения работы тренажёров. Продолжая использовать сайт, вы соглашаетесь с нашей <a href="/math-6-grade/privacy.html" style="color:#4DA8DA; text-decoration:underline;">Политикой конфиденциальности</a>.</div>
            <button id="accept-cookie-btn" style="background:#4DA8DA; color:#fff; border:none; padding:8px 20px; border-radius:20px; cursor:pointer; font-weight:bold; transition:0.2s;">Понятно</button>
        `;
        document.body.appendChild(cookieBanner);
        document.getElementById('accept-cookie-btn').onclick = function() {
            localStorage.setItem('cookieConsentAccepted', 'true');
            cookieBanner.style.opacity = '0';
            setTimeout(() => cookieBanner.remove(), 300);
        };
    }
});