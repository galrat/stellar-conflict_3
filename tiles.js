'use strict';
// ══════════════════════════════════════════════════════════════════════
//  tiles.js — каталог системных тайлов  Stellar Conflict
//
//  Каждый тайл имеет две стороны (A и B).
//  Все параметры хранятся в матрицах 2×2:
//    [строка 0 = верх][столбец 0 = лево]
//    [строка 1 = низ ][столбец 1 = право]
//  Индексы областей (area index 0..3):
//    0 = [0][0] верх-лево     1 = [0][1] верх-право
//    2 = [1][0] низ-лево      3 = [1][1] низ-право
//
//  layout:   1 = планета, 0 = пустота (космос без планеты)
//  capacity: вместимость (1–3 для планет, всегда 3 для пустот)
//  income:   доход ресурсов за раунд — зелёный кружок (0–3 для планет, 0 для пустот)
//  valuable: ценные ресурсы        — красный кружок  (0–3 для планет, 0 для пустот)
//  support:  жетон поддержки  — 1 = есть, 0 = нет
//  discount: жетон скидки     — 1 = есть, 0 = нет
//  forge:    жетон молотка    — 1 = есть, 0 = нет
//  joker:    жетон джокера    — 1 = есть, 0 = нет
//  image:    путь к PNG-изображению стороны тайла
//
//  После вращения тайла области (и все их параметры) вращаются вместе
//  через таблицу RMAP — см. game_engine.html.
// ══════════════════════════════════════════════════════════════════════

let TILE_CATALOG = [

  // ── Домашние системы фракций (HOME): 3 планеты + 1 пустота ──────────
  // Каждая фракция имеет свой уникальный домашний тайл.
  // Данные — заготовки; заполни реальными значениями под каждую фракцию.
  // Изображения: tiles/home_<faction_id>_a.png / _b.png

  //==================================================
  // базовые 4 фракции
  {
    id: 'home_chaos', tileNum: 'H-Хаос', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_chaos_a.png',
        layout:   [[1, 1], [0, 1]],
        capacity: [[4, 3], [3, 3]],
        income:   [[1, 1], [0, 1]],
        valuable: [[0, 1], [0, 1]],
        support:  [[0, 1], [0, 0]],
        discount: [[0, 0], [0, 1]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_chaos_b.png',
        layout:   [[1, 1], [0, 1]],
        capacity: [[3, 4], [3, 3]],
        income:   [[2, 0], [0, 1]],
        valuable: [[0, 1], [0, 1]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 1]],
        forge:    [[0, 1], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_orks', tileNum: 'H-Орки', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_orks_a.png',
        layout:   [[1, 0], [1, 1]],
        capacity: [[4, 3], [4, 2]],
        income:   [[0, 0], [1, 2]],
        valuable: [[1, 0], [0, 1]],
        support:  [[0, 0], [0, 1]],
        discount: [[0, 0], [0, 0]],
        forge:    [[1, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_orks_b.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[4, 3], [3, 3]],
        income:   [[1, 1], [1, 0]],
        valuable: [[0, 1], [1, 0]],
        support:  [[0, 1], [0, 0]],
        discount: [[0, 0], [1, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_marine', tileNum: 'H-Маринесы', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_marine_a.png',
        layout:   [[1, 0], [1, 1]],
        capacity: [[2, 3], [4, 4]],
        income:   [[2, 0], [0, 1]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [2, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_marine_b.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[4, 3], [3, 3]],
        income:   [[0, 1], [2, 0]],
        valuable: [[2, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[2, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_eldar', tileNum: 'H-Эльдары', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_eldar_a.png',
        layout:   [[1, 1], [0, 0]],
        capacity: [[3, 4], [3, 3]],
        income:   [[1, 2], [0, 0]],
        valuable: [[2, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[1, 0], [0, 1]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[1, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_eldar_b.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[3, 3], [3, 4]],
        income:   [[1, 0], [0, 2]],
        valuable: [[2, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[1, 0], [0, 0]],
        joker:    [[1, 0], [0, 0]],
      },
    ],
  },

  // =================================================
  // первый доп

  {
    id: 'home_empire', tileNum: 'H-Империя', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_empire_a.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[3, 2], [1, 3]],
        income:   [[1, 2], [1, 0]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[1, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_empire_b.png',
        layout:   [[1, 1], [0, 1]],
        capacity: [[2, 3], [3, 1]],
        income:   [[2, 1], [0, 1]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 1]],
        forge:    [[1, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },



  {
    id: 'home_syndicate', tileNum: 'H-Синдикат', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_syndicate_a.png',
        layout:   [[1, 0], [1, 1]],
        capacity: [[1, 3], [1, 2]],
        income:   [[2, 0], [1, 2]],
        valuable: [[0, 0], [0, 0]],
        support:  [[1, 0], [0, 0]],
        discount: [[0, 0], [1, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_syndicate_b.png',
        layout:   [[1, 1], [0, 1]],
        capacity: [[2, 1], [3, 1]],
        income:   [[2, 2], [0, 1]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 1], [0, 0]],
        discount: [[1, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_nomads', tileNum: 'H-Кочевники', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_nomads_a.png',
        layout:   [[1, 0], [1, 1]],
        capacity: [[1, 3], [2, 1]],
        income:   [[1, 0], [2, 1]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [1, 0]],
        discount: [[1, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_nomads_b.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[1, 2], [1, 3]],
        income:   [[1, 2], [1, 0]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 1], [0, 0]],
        forge:    [[0, 0], [1, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_elders', tileNum: 'H-Предтечи', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_elders_a.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[1, 1], [1, 3]],
        income:   [[3, 2], [2, 0]],
        valuable: [[0, 0], [0, 0]],
        support:  [[1, 0], [0, 0]],
        discount: [[0, 1], [0, 0]],
        forge:    [[0, 0], [1, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_elders_b.png',
        layout:   [[1, 0], [1, 1]],
        capacity: [[1, 3], [1, 1]],
        income:   [[2, 0], [3, 2]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [1, 0]],
        discount: [[1, 0], [0, 1]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_traders', tileNum: 'H-Торговый союз', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_traders_a.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[1, 2], [1, 3]],
        income:   [[3, 2], [2, 0]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[1, 1], [1, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_traders_b.png',
        layout:   [[1, 1], [0, 1]],
        capacity: [[2, 1], [3, 1]],
        income:   [[2, 3], [0, 2]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[1, 0], [0, 1]],
        forge:    [[0, 1], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'home_mutants', tileNum: 'H-Мутанты', isHome: true,
    sides: [
      {
        side: 'a', image: 'tiles/home_mutants_a.png',
        layout:   [[1, 1], [1, 0]],
        capacity: [[3, 1], [2, 3]],
        income:   [[1, 1], [2, 0]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 1], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[1, 0], [1, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/home_mutants_b.png',
        layout:   [[1, 0], [1, 1]],
        capacity: [[2, 3], [3, 1]],
        income:   [[2, 0], [1, 1]],
        valuable: [[0, 0], [0, 0]],
        support:  [[0, 0], [0, 1]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [1, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },





  // ── Обычные системы (NORMAL): 8 тайлов, 2 планеты + 2 пустоты ───────

  {
    id: 'normal_01', tileNum: 1, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_01_a.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[3, 3], [3, 3]],
        income:   [[1, 0], [0, 2]],
        valuable: [[1, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[1, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_01_b.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[2, 3], [3,4]],
        income:   [[2, 0], [0, 0]],
        valuable: [[1, 0], [0, 1]],
        support:  [[1, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 1]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'normal_02', tileNum: 2, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_02_a.png',
        layout:   [[1, 1], [0, 0]],
        capacity: [[5, 1], [3, 3]],
        income:   [[0, 3], [0, 0]],
        valuable: [[1, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[1, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_02_b.png',
        layout:   [[0, 0], [1, 1]],
        capacity: [[3, 3], [4, 3]],
        income:   [[0, 0], [2, 0]],
        valuable: [[0, 0], [0, 2]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 2]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'normal_03', tileNum: 3, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_03_a.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[2, 3], [3, 4]],
        income:   [[2, 0], [0, 1]],
        valuable: [[1, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[1, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_03_b.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[2, 3], [3, 4]],
        income:   [[2, 0], [0, 0]],
        valuable: [[1, 0], [0, 1]],
        support:  [[0, 0], [0, 0]],
        discount: [[1, 0], [0, 0]],
        forge:    [[0, 0], [0, 1]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'normal_04', tileNum: 4, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_04_a.png',
        layout:   [[1, 1], [0, 0]],
        capacity: [[1, 3], [3, 3]],
        income:   [[1, 1], [0, 0]],
        valuable: [[1, 1], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 1], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[1, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_04_b.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[2, 3], [3, 2]],
        income:   [[1, 0], [0, 1]],
        valuable: [[1, 0], [0, 1]],
        support:  [[0, 0], [0, 0]],
        discount: [[1, 0], [0, 1]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'normal_05', tileNum: 5, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_05_a.png',
        layout:   [[0, 0], [1, 1]],
        capacity: [[3, 3], [2, 4]],
        income:   [[0, 0], [2, 1]],
        valuable: [[1, 0], [0, 0]],
        support:  [[1, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_05_b.png',
        layout:   [[1, 1], [0, 0]],
        capacity: [[3, 3], [3, 3]],
        income:   [[1, 1], [0, 0]],
        valuable: [[1, 1], [0, 0]],
        support:  [[1, 0], [0, 0]],
        discount: [[0, 1], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'normal_06', tileNum: 6, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_06_a.png',
        layout:   [[0, 1], [1, 0]],
        capacity: [[3, 3], [3, 3]],
        income:   [[0, 1], [1, 0]],
        valuable: [[0, 1], [1, 0]],
        support:  [[0, 1], [1, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_06_b.png',
        layout:   [[0, 1], [1, 0]],
        capacity: [[3, 3], [1, 3]],
        income:   [[0, 1], [1, 0]],
        valuable: [[0, 1], [1, 0]],
        support:  [[0, 1], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [1, 0]],
      },
    ],
  },

  {
    id: 'normal_07', tileNum: 7, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_07_a.png',
        layout:   [[1, 1], [0, 0]],
        capacity: [[3, 2], [3, 3]],
        income:   [[2, 0], [0, 0]],
        valuable: [[0, 0], [0, 2]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 1], [0, 0]],
        forge:    [[0, 1], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_07_b.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[2, 3], [3, 3]],
        income:   [[0, 0], [0, 2]],
        valuable: [[2, 0], [0, 0]],
        support:  [[1, 0], [0, 0]],
        discount: [[1, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[0, 0], [0, 0]],
      },
    ],
  },

  {
    id: 'normal_08', tileNum: 8, isHome: false,
    sides: [
      {
        side: 'a', image: 'tiles/normal_08_a.png',
        layout:   [[0, 0], [1, 1]],
        capacity: [[3, 3], [3, 1]],
        income:   [[0, 0], [0, 3]],
        valuable: [[1, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[1, 0], [0, 0]],
      },
      {
        side: 'b', image: 'tiles/normal_08_b.png',
        layout:   [[1, 0], [0, 1]],
        capacity: [[3, 3], [3, 1]],
        income:   [[0, 0], [0, 3]],
        valuable: [[1, 0], [0, 0]],
        support:  [[0, 0], [0, 0]],
        discount: [[0, 0], [0, 0]],
        forge:    [[0, 0], [0, 0]],
        joker:    [[1, 0], [0, 0]],
      },
    ],
  },

];

// ── Конвертирует сторону тайла из формата 2×2 в плоский массив 4 областей ──
// Порядок областей: [0][0], [0][1], [1][0], [1][1]
// = верх-лево, верх-право, низ-лево, низ-право (area index 0..3)
// Этот порядок совпадает с RMAP в game_engine.html.
function tileDefToAreas(side) {
  const out = [];
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 2; c++) {
      const isPlanet = side.layout[r][c] === 1;
      out.push({
        area_place: r * 2 + c,
        type:     isPlanet ? 'planet' : 'space',
        capacity: side.capacity[r][c],
        income:   side.income[r][c],
        valuable: side.valuable[r][c],
        support:  side.support[r][c],
        discount: side.discount[r][c],
        forge:    side.forge[r][c],
        joker:    side.joker[r][c],
        troops:     [],
        structures: [],
      });
    }
  }
  return out;
}
