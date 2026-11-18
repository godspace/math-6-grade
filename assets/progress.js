// Файл: assets/progress.js — рисует реальный прогресс миссий на лендинге (§23.6).
// Читает MissionStore (assets/analytics.js) и манифест зон (assets/missions.js).
(function () {
    'use strict';

    var WARNED = {};

    function warnOnce(id) {
        if (WARNED[id]) return;
        WARNED[id] = true;
        console.warn('[progress] неизвестная миссия:', id);
    }

    function missionState(id) {
        var store = window.MissionStore;
        if (!store || !id) return 'none';
        var entry = store.get(id);
        if (!entry) return 'none';
        if (entry.d) return 'done';
        if (entry.w > 0 || entry.s) return 'active';
        return 'none';
    }

    function zoneTitle(box) {
        var card = box.closest ? box.closest('.zone-card') : null;
        var title = card ? card.querySelector('.zone-title') : null;
        return title ? title.textContent.trim() : '';
    }

    function renderZone(name, ids) {
        var box = document.querySelector('[data-progress="' + name + '"]');
        if (!box) return;
        var total = ids.length;
        var done = 0;
        var active = 0;
        ids.forEach(function (id) {
            var st = missionState(id);
            if (st === 'done') done++;
            else if (st === 'active') active++;
        });
        var label = box.querySelector('[data-progress-label]');
        if (label) label.textContent = done + ' / ' + total + (active ? ' · ' + active + ' в процессе' : '');
        var fill = box.querySelector('[data-progress-fill]');
        var activeFill = box.querySelector('[data-progress-active]');
        if (fill) fill.style.width = (total ? done * 100 / total : 0) + '%';
        if (activeFill) activeFill.style.width = (total ? active * 100 / total : 0) + '%';
        var track = box.querySelector('.progress-track');
        if (track) {
            track.setAttribute('role', 'progressbar');
            track.setAttribute('aria-valuemin', '0');
            track.setAttribute('aria-valuemax', String(total));
            track.setAttribute('aria-valuenow', String(done));
            track.setAttribute('aria-label', 'Прогресс миссий: ' + (zoneTitle(box) || name));
        }
    }

    function renderMissions(known, external) {
        var links = document.querySelectorAll('a[data-mission]');
        Array.prototype.forEach.call(links, function (link) {
            var id = link.getAttribute('data-mission');
            if (external[id]) {
                link.classList.remove('is-done', 'is-active');
                return;
            }
            if (!known[id]) {
                warnOnce(id);
                return;
            }
            var st = missionState(id);
            link.classList.toggle('is-done', st === 'done');
            link.classList.toggle('is-active', st === 'active');
        });
    }

    function render() {
        var zones = window.MG6_ZONES;
        if (!zones) {
            console.warn('[progress] манифест MG6_ZONES не найден — прогресс не отрисован');
            return;
        }
        var known = {};
        Object.keys(zones).forEach(function (name) {
            zones[name].forEach(function (id) { known[id] = name; });
            renderZone(name, zones[name]);
        });
        var external = {};
        (window.MG6_EXTERNAL || []).forEach(function (id) { external[id] = true; });
        renderMissions(known, external);
        document.body.dataset.progressReady = '1';
    }

    function onChange(event) {
        var key = window.MissionStore && window.MissionStore.KEY;
        if (!event || !event.key || event.key === key) render();
    }

    function start() {
        render();
        window.addEventListener('storage', onChange);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
    else start();
})();
