// Файл: assets/trainers-utils.js
// Общие утилиты страниц-тренажёров. Подключается обычным <script> без defer,
// чтобы inline-скрипт страницы видел функции к моменту выполнения.
// Правило: сюда переносится только идентичный код; варианты тела остаются в страницах (§14.2 п.1).

// --- Вибрация (мобильные устройства) ---
function vibrate(ms) { if ('vibrate' in navigator) navigator.vibrate(ms); }

// --- Делимость ---
function isPrime(num) {
  if (num < 2) return false;
  for (let i = 2; i <= Math.sqrt(num); i++) {
    if (num % i === 0) return false;
  }
  return true;
}

function gcd(a, b) { return !b ? a : gcd(b, a % b); }
function lcm(a, b) { return (a * b) / gcd(a, b); }

function primeFactors(num) {
  let factors = [];
  let d = 2;
  while (num >= 2) {
    if (num % d === 0) { factors.push(d); num /= d; } else { d++; }
  }
  return factors;
}
