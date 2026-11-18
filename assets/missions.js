// Файл: assets/missions.js — состав зон лендинга (порядок = порядок в разметке).
// Тексты и href берутся из DOM по a[data-mission]; здесь только id (§23.5).
window.MG6_ZONES = {
    equations:    ['opening', 'opening_test', 'equations_constructor', 'equations_test', 'equations_construct', 'equations_construct_2'],
    fractions:    ['fraction_conversion', 'fraction_comparison', 'fraction_addition', 'fraction_multiplication', 'fraction_division', 'fraction_mixed', 'mixed_complex'],
    divisibility: ['primes', 'divisibility_signs', 'gcd', 'lcm'],
    geometry:     ['pi', 'area_metaphor', 'area_constructor', 'perimeter_area'],
    percents:     ['percent_of', 'number_by', 'ratio', 'percent_tiles', 'base_change'],
    rational:     ['motion', 'coordinates_pro', 'phone_balance'],
    survival:     ['vpr']
};

// Внешние миссии: в разметке помечены data-mission, но в знаменатель не входят (§23.1).
window.MG6_EXTERNAL = ['business'];

// Без прогресса по существу: песочница без цели и финального экрана (§23.7, P3).
window.MG6_UNTRACKED = ['math_board'];
