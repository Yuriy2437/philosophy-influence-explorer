# Контрольная проверка семантического поиска

Дата: 2026-10-18.

## Проверяемая рабочая точка

- Реализация Gemini-провайдера: коммит `f083a91`.
- Предшествующая запись журнала: коммит `b15b163`.
- Проверка выполнена вручную через интерфейс приложения в Vercel.
- Модель: `gemini-embedding-001`.
- Размерность: 768.
- Корпус: 16 passages из `curated_corpus_v1`.
- Векторный индекс Aura: `passage_embedding_index`, ONLINE.
- Результаты ниже перенесены из вывода интерфейса.
- Оценки Similarity приведены с точностью отображения интерфейса.

## 1. Положительная проверка известной цитаты

Запрос:

> So act as to treat humanity, whether in thine own person or in that of any other

Общие настройки обоих запусков:

- Concept family: All.
- Language: EN / English.
- Maximum results: 3.

Ожидаемый passage:

`passage:kant:groundwork:2:humanity:en`

Источник: `source:kant:gutenberg-5682`.

Citation: Fundamental Principles of the Metaphysic of Morals,
Second Section (Abbott translation).

| Запуск | Provenance filter | Позиция ожидаемого passage | Similarity |
|---|---|---:|---:|
| P1 | All | 1 | 0.898 |
| P2 | Primary quotations only | 1 | 0.898 |

В обоих запусках порядок результатов совпал:

1. `passage:kant:groundwork:2:humanity:en` — 0.898.
2. `passage:kant:groundwork:2:autonomy:en` — 0.838.
3. `passage:mill:on-liberty:1:harm:en` — 0.822.

Все три записи отображались как Primary quotation, Non-editorial,
EN, text_kind = primary_quote, Review: candidate.

Результат: известная цитата найдена первой и сохраняется при
включении фильтра первичных цитат.

Ограничение: исходная тройка уже состояла из первичных цитат,
поэтому совпадение двух выдач само по себе не проверяет исключение
редакционных материалов. Такая отрицательная проверка была выполнена
ранее: для запроса о диалектике и познании при Concept family =
epistemology, Language = EN и Primary quotations only редакционные
резюме исчезли, интерфейс показал пустую выдачу.

## 2. Контрольные смысловые запросы Q1–Q6

Настройки подтверждены пользователем для всех шести запросов:

- Concept family: All.
- Language: All.
- Maximum results: 3.
- Provenance filter: Primary quotations only.

Ожидаемые passages определены до запуска по выгрузке корпуса.

### Q1 — Человек как цель

Запрос:

> Why should a person be treated as an end rather than merely as a means?

Ожидаемый passage: `passage:kant:groundwork:2:humanity:en`.

Фактическая выдача:

1. `passage:kant:groundwork:2:humanity:en` — 0.861.
2. `passage:mill:on-liberty:3:individuality:en` — 0.818.
3. `passage:mill:on-liberty:1:harm:en` — 0.807.

### Q2 — Автономия воли

Запрос:

> What does it mean for the will to give itself a universal law?

Ожидаемый passage: `passage:kant:groundwork:2:autonomy:en`.

Фактическая выдача:

1. `passage:kant:groundwork:2:autonomy:en` — 0.888.
2. `passage:kant:groundwork:2:humanity:en` — 0.840.
3. `passage:mill:on-liberty:1:harm:en` — 0.809.

### Q3 — Допустимость принуждения

Запрос:

> When is it legitimate to exercise power over someone against their will?

Ожидаемый passage: `passage:mill:on-liberty:1:harm:en`.

Фактическая выдача:

1. `passage:mill:on-liberty:1:harm:en` — 0.863.
2. `passage:kant:groundwork:2:autonomy:en` — 0.803.
3. `passage:mill:on-liberty:3:individuality:en` — 0.800.

### Q4 — Индивидуальность и развитие

Запрос:

> How does the cultivation of individuality contribute to human development?

Ожидаемый passage: `passage:mill:on-liberty:3:individuality:en`.

Фактическая выдача:

1. `passage:mill:on-liberty:3:individuality:en` — 0.869.
2. `passage:mill:on-liberty:1:harm:en` — 0.791.
3. `passage:kant:groundwork:2:humanity:en` — 0.790.

### Q5 — Становление, бытие и ничто

Запрос:

> How is becoming related to being and nothing?

Ожидаемый passage: `passage:hegel:wl:being:de`.

Фактическая выдача:

1. `passage:hegel:wl:being:de` — 0.854.
2. `passage:cusanus:ddi:1.4:la` — 0.801.
3. `passage:cusanus:ddi:1.1:la` — 0.785.

Проверенный межъязыковой случай: английский запрос,
ожидаемый passage на немецком.

### Q6 — Бесконечное и пропорция

Запрос:

> Почему бесконечное нельзя постичь через сравнение и пропорцию?

Ожидаемый passage: `passage:cusanus:ddi:1.1:la`.

Фактическая выдача:

1. `passage:cusanus:ddi:1.1:la` — 0.876.
2. `passage:cusanus:ddi:1.4:la` — 0.821.
3. `passage:hegel:wl:being:de` — 0.785.

Проверенный межъязыковой случай: русский запрос,
ожидаемый passage на латыни.

## 3. Итог и границы проверки

- Во всех шести смысловых запросах ожидаемый passage найден
  на первом месте: 6 из 6.
- Известная цитата Канта найдена первой в обоих запусках P1/P2.
- Во всех показанных результатах Q1–Q6 сохраняется маркировка
  первичных, нередакционных цитат.
- Показанные записи Канта и Милля имеют Review: candidate.
- Показанные записи Гегеля и Кузанского имеют Review: reviewed.
- Фильтр Primary quotations only не означает фильтрацию
  по статусу научной проверки: candidate остаются в выдаче.
- Нахождение ожидаемого passage не равнозначно полноте ответа.
  В частности, Q1 запрашивает обоснование, а найденный фрагмент
  формулирует требование; подробное обоснование в нём не представлено.
- Полная экспертная оценка релевантности всех трёх результатов
  каждого запроса ещё не выполнена.
- Набор мал и составлен по известному корпусу; результат нельзя
  переносить на произвольные вопросы или более крупный корпус.
- Q5 и Q6 подтверждают два конкретных межъязыковых случая,
  но не универсальное качество межъязыкового поиска.
- Similarity — оценка сходства, а не вероятность истинности.
- Полнота выдачи при фильтрации после отбора векторных кандидатов
  отдельно не проверена.
- Точность цитат и статус перевода требуют самостоятельной
  источниковедческой проверки.

## 4. Следующие задачи

1. Выполнить экспертную оценку каждого результата:
   прямо релевантен, частично релевантен, тематически близок
   или нерелевантен.
2. Добавить независимые перефразирования и вопросы вне корпуса.
3. Проверить полноту фильтрованного поиска.
4. Отдельно проверить и при необходимости обновить статусы
   научной проверки записей candidate.
