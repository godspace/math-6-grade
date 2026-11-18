// Файл: assets/trainer-core.js
// Каркас новых тренажёров «Проценты и пропорции» (PROJECT_OPTIMIZATION_PLAN.md §22.3).
// Подключается обычным <script> без defer после assets/trainers-utils.js и до
// assets/analytics.js (defer). Ядро владеет уровнями, счётом, кнопками,
// обратной связью, победой/конфетти и RewardSystem; страница отдаёт только
// generate/render/check и свой визуал. Чистые утилиты — в trainers-utils.js.

window.TrainerCore = (function () {
    'use strict';

    var TASKS_PER_LEVEL = 1;   // схема «5 уровней по 1 задаче» (§22.2)
    var TOLERANCE = 0.005;     // допуск сравнения ответа, ответы до сотых (§22.5)
    var MAX_TRIES = 200;       // лимит перегенерации «некрасивых» пар (§22.4)
    var REWARD_DELAY = 1000;   // задержка лутбокса, как в существующих тренажёрах
    var CONFETTI_COLORS = ['#4361ee', '#f72585', '#2ec4b6', '#ff9f1c', '#4834d4'];

    var cfg = null;
    var state = null;
    var refs = {};
    var ready = false;
    var confettiId = null;

    function byId(id) { return document.getElementById(id); }

    function isVisible(node) {
        return !!node && node.style.display !== 'none' && !node.hidden;
    }

    // «12,5» и «12.5» — одно и то же; пустое/мусор → null (§22.5)
    function parseNumber(raw) {
        if (raw === null || raw === undefined) return null;
        var text = String(raw).replace(',', '.').replace(/\s+/g, '');
        if (!text) return null;
        var value = Number(text);
        return isFinite(value) ? value : null;
    }

    function close(value, expected, tolerance) {
        if (typeof value !== 'number' || !isFinite(value)) return false;
        var eps = typeof tolerance === 'number' ? tolerance : TOLERANCE;
        return Math.abs(value - expected) <= eps + 1e-9;
    }

    // Ответ «красивый»: целое или конечная десятичная с ≤2 знаками (§22.4)
    function isNiceAnswer(value) {
        if (typeof value !== 'number' || !isFinite(value)) return false;
        return Math.abs(value * 100 - Math.round(value * 100)) < 1e-9;
    }

    // Canvas под devicePixelRatio: возвращает контекст в CSS-координатах (§22.7)
    function fitCanvas(canvas) {
        if (!canvas) return null;
        var ratio = window.devicePixelRatio || 1;
        var rect = canvas.getBoundingClientRect();
        var width = Math.max(1, Math.round(rect.width || canvas.clientWidth || 300));
        var height = Math.max(1, Math.round(rect.height || canvas.clientHeight || 150));
        canvas.width = Math.round(width * ratio);
        canvas.height = Math.round(height * ratio);
        var ctx = canvas.getContext('2d');
        if (ctx) ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        return ctx;
    }

    function clearCanvas(canvas) {
        if (!canvas) return null;
        var ctx = canvas.getContext('2d');
        if (!ctx) return null;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return ctx;
    }

    // --- Разметка каркаса ---
    function buildChrome() {
        var container = document.querySelector('.container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'container';
            document.body.appendChild(container);
        }

        var header = container.querySelector('.header');
        if (!header) {
            header = document.createElement('div');
            header.className = 'header';
            container.insertBefore(header, container.firstChild);
            var titleBox = document.createElement('div');
            titleBox.innerHTML = '<h1>' + (cfg.title || 'Тренажёр') + '</h1>' +
                '<div class="subtitle" id="levelDescription"></div>';
            header.appendChild(titleBox);
        }

        var badges = document.createElement('div');
        badges.className = 'level-badges';
        for (var i = 1; i <= cfg.totalLevels; i++) {
            var badge = document.createElement('div');
            badge.className = 'lvl-badge';
            badge.textContent = String(i);
            badges.appendChild(badge);
        }
        header.appendChild(badges);

        var stats = document.createElement('div');
        stats.className = 'stats-box';
        stats.innerHTML = 'Счёт: <span id="score">0</span> | Ошибки: <span id="errors">0</span>';
        header.appendChild(stats);

        var root = byId('trainerRoot');
        if (!root) {
            root = document.createElement('div');
            root.id = 'trainerRoot';
            container.appendChild(root);
        }

        root.innerHTML = [
            '<div class="kids-guide" id="kidsGuide"></div>',
            '<div class="work-area">',
            '  <div class="visual-container" id="taskVisual"></div>',
            '  <div class="task-statement" id="taskStatement"></div>',
            '  <div class="answer-row">',
            '    <input class="answer-input" id="answerInput" type="text" inputmode="decimal"',
            '           autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Ответ">',
            '    <span class="answer-unit" id="answerUnit"></span>',
            '  </div>',
            '</div>',
            '<div class="actions">',
            '  <div class="feedback" id="feedbackMsg"></div>',
            '  <button class="btn btn-check" id="checkBtn" type="button">Проверить</button>',
            '  <button class="btn btn-next" id="nextBtn" type="button">Следующий уровень ➡</button>',
            '</div>',
            '<div class="victory-modal" id="victoryScreen">',
            '  <canvas id="confettiCanvas"></canvas>',
            '  <div class="trophy">🏆</div>',
            '  <h2>Все уровни пройдены!</h2>',
            '  <div class="victory-stats">Верных решений: <b id="finalScore">0</b><br>Ошибок: <b id="finalErrors">0</b></div>',
            '  <button class="btn" id="restartBtn" type="button">Начать заново</button>',
            '</div>'
        ].join('\n');

        var guideBox = byId('kidsGuide');
        (cfg.guide || []).forEach(function (text, index) {
            var step = document.createElement('div');
            step.className = 'guide-step';
            step.innerHTML = '<div class="step-num">' + (index + 1) + '</div><div>' + text + '</div>';
            guideBox.appendChild(step);
        });

        refs.guide = guideBox;
        refs.visual = byId('taskVisual');
        refs.statement = byId('taskStatement');
        refs.input = byId('answerInput');
        refs.unit = byId('answerUnit');
        refs.checkBtn = byId('checkBtn');
        refs.nextBtn = byId('nextBtn');
        refs.feedback = byId('feedbackMsg');
        refs.victory = byId('victoryScreen');
        refs.restartBtn = byId('restartBtn');
        refs.score = byId('score');
        refs.errors = byId('errors');
        refs.subtitle = byId('levelDescription');

        refs.checkBtn.addEventListener('click', checkAnswer);
        refs.nextBtn.addEventListener('click', nextTask);
        refs.restartBtn.addEventListener('click', function () { window.location.reload(); });
        refs.input.addEventListener('input', function () { updateCheckState(); });
        document.addEventListener('keydown', onKeyDown);
    }

    // --- Уровни и задачи ---
    function levelConfig() { return (cfg.level && cfg.level(state.level)) || {}; }

    function renderLevel() {
        var badges = document.querySelectorAll('.lvl-badge');
        for (var i = 0; i < badges.length; i++) {
            var number = i + 1;
            badges[i].classList.toggle('completed', number < state.level);
            badges[i].classList.toggle('active', number === state.level);
        }
        var meta = levelConfig();
        if (refs.subtitle) {
            refs.subtitle.textContent = 'Задание ' + state.level + ' из ' + cfg.totalLevels +
                (meta.desc ? ' · ' + meta.desc : '');
        }
        newTask();
    }

    function newTask() {
        var meta = levelConfig();
        state.task = meta.generate();
        state.solvedInLevel = 0;

        refs.statement.innerHTML = state.task.text || '';
        refs.unit.textContent = state.task.unit || '';
        refs.input.value = '';
        refs.input.disabled = false;
        refs.input.classList.remove('correct', 'wrong');
        refs.feedback.textContent = '';
        refs.feedback.className = 'feedback';
        refs.nextBtn.style.display = 'none';
        refs.checkBtn.style.display = 'inline-flex';
        updateCheckState();
        refs.visual.innerHTML = '';

        if (typeof meta.render === 'function') meta.render(state.task);
        animateTaskIntro();

        if (window.RewardSystem) window.RewardSystem.resetErrors();

        if (!ready) {
            ready = true;
            document.body.dataset.trainerReady = '1';
            if (typeof cfg.onReady === 'function') cfg.onReady();
        }
    }

    function animateTaskIntro() {
        refs.statement.classList.remove('intro');
        void refs.statement.offsetWidth; // перезапуск CSS-анимации
        refs.statement.classList.add('intro');
    }

    function updateCheckState() {
        var value = parseNumber(refs.input.value);
        if (!state.finished) refs.checkBtn.disabled = value === null;
    }

    function updateStats() {
        refs.score.textContent = String(state.score);
        refs.errors.textContent = String(state.errors);
    }

    function setFeedback(message, type) {
        refs.feedback.textContent = message || '';
        refs.feedback.className = 'feedback' + (type ? ' ' + type : '');
    }

    function checkAnswer() {
        if (!state || state.finished || !isVisible(refs.checkBtn)) return;
        var value = parseNumber(refs.input.value);
        if (value === null) { setFeedback('Введи ответ числом — можно с запятой.', 'err'); return; }

        var meta = levelConfig();
        var ok = typeof meta.check === 'function'
            ? meta.check(state.task, value, refs.input.value)
            : close(value, state.task.answer);

        if (ok) handleCorrect(); else handleWrong();
    }

    function handleCorrect() {
        state.score++;
        state.solvedInLevel++;
        updateStats();
        refs.input.classList.remove('wrong');
        refs.input.classList.add('correct');
        refs.input.disabled = true;
        refs.checkBtn.style.display = 'none';
        refs.nextBtn.style.display = 'inline-flex';
        refs.nextBtn.textContent = state.level < cfg.totalLevels
            ? 'Следующий уровень 🆙'
            : 'Получить сертификат 🏆';
        setFeedback(state.task.explain ? 'Верно! ' + state.task.explain : 'Верно!', 'ok');
        if (typeof vibrate === 'function') vibrate(20);

        if (window.RewardSystem && state.level < cfg.totalLevels) {
            window.setTimeout(function () {
                if (window.RewardSystem) {
                    window.RewardSystem.showWin('Уровень ' + state.level + ' пройден!', cfg.id);
                }
            }, REWARD_DELAY);
        }
    }

    function handleWrong() {
        state.errors++;
        updateStats();
        refs.input.classList.remove('correct');
        refs.input.classList.add('wrong');
        window.setTimeout(function () { refs.input.classList.remove('wrong'); }, 500);
        setFeedback('Пока неверно. Проверь, что принимаем за 100%, и попробуй ещё раз.', 'err');
        if (window.RewardSystem) window.RewardSystem.registerError(cfg.id);
        if (typeof vibrate === 'function') vibrate(35);
    }

    function nextTask() {
        if (!state || state.finished || !isVisible(refs.nextBtn)) return;
        if (state.solvedInLevel < TASKS_PER_LEVEL) return;
        if (state.level >= cfg.totalLevels) { showVictory(); return; }
        state.level++;
        renderLevel();
    }

    function onKeyDown(event) {
        if (event.key !== 'Enter' || event.isComposing) return;
        if (state && state.finished) return;
        if (isVisible(refs.nextBtn)) { event.preventDefault(); nextTask(); return; }
        if (isVisible(refs.checkBtn) && !refs.checkBtn.disabled) {
            event.preventDefault();
            checkAnswer();
        }
    }

    // --- Победа и конфетти (живут только в каркасе, §22.7) ---
    function showVictory() {
        if (!state || state.finished) return;
        state.finished = true;
        var finalScore = byId('finalScore');
        var finalErrors = byId('finalErrors');
        if (finalScore) finalScore.textContent = String(state.score);
        if (finalErrors) finalErrors.textContent = String(state.errors);
        refs.checkBtn.style.display = 'none';
        refs.nextBtn.style.display = 'none';
        refs.input.disabled = true;
        refs.victory.classList.add('active');
        if (window.RewardSystem) {
            window.RewardSystem.showWin('Все ' + cfg.totalLevels + ' уровней пройдены!', cfg.id);
        }
        startConfetti();
    }

    function startConfetti() {
        var canvas = byId('confettiCanvas');
        if (!canvas) return;
        var ctx = fitCanvas(canvas);
        if (!ctx) return;
        var width = canvas.clientWidth || 600;
        var height = canvas.clientHeight || 400;
        var pieces = [];
        for (var i = 0; i < 150; i++) {
            pieces.push({
                x: Math.random() * width,
                y: Math.random() * -height,
                w: 6 + Math.random() * 6,
                h: 8 + Math.random() * 8,
                vy: 1.5 + Math.random() * 3,
                vx: -1 + Math.random() * 2,
                angle: Math.random() * Math.PI,
                spin: -0.1 + Math.random() * 0.2,
                color: CONFETTI_COLORS[i % CONFETTI_COLORS.length]
            });
        }
        var deadline = Date.now() + 6000;
        window.cancelAnimationFrame(confettiId);

        function frame() {
            clearCanvas(canvas);
            for (var i = 0; i < pieces.length; i++) {
                var piece = pieces[i];
                piece.x += piece.vx;
                piece.y += piece.vy;
                piece.angle += piece.spin;
                if (piece.y > height + 20) {
                    piece.y = -20;
                    piece.x = Math.random() * width;
                }
                ctx.save();
                ctx.translate(piece.x, piece.y);
                ctx.rotate(piece.angle);
                ctx.fillStyle = piece.color;
                ctx.fillRect(-piece.w / 2, -piece.h / 2, piece.w, piece.h);
                ctx.restore();
            }
            if (Date.now() < deadline) {
                confettiId = window.requestAnimationFrame(frame);
            } else {
                clearCanvas(canvas);
            }
        }
        frame();
    }

    // --- Единственный вход каркаса (§22.3) ---
    function init(config) {
        if (!config || typeof config.level !== 'function') {
            throw new Error('TrainerCore.init: нужен config.level(n)');
        }
        cfg = {
            id: config.id || 'trainer',
            title: config.title || '',
            totalLevels: config.totalLevels || 5,
            guide: config.guide || [],
            level: config.level,
            onReady: config.onReady
        };
        state = { level: 1, score: 0, errors: 0, task: null, solvedInLevel: 0, finished: false };
        buildChrome();
        updateStats();
        renderLevel();
        return api;
    }

    var api = {
        init: init,
        parseNumber: parseNumber,
        close: close,
        isNiceAnswer: isNiceAnswer,
        fitCanvas: fitCanvas,
        clearCanvas: clearCanvas,
        TOLERANCE: TOLERANCE,
        MAX_TRIES: MAX_TRIES
    };

    return api;
})();
