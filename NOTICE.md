# Attribution

Humanizer RU Pro включает переработанные идеи и элементы структуры из двух MIT-лицензированных проектов:

1. `ilyautov/humanizer-ru`
   - Copyright (c) 2026 Ilya Utov
2. `Vladimir-Human/humanizer-ru`
   - Copyright (c) 2026 Vladimir

Оригинальные copyright notices и условия MIT License сохраняются в этом репозитории.

Книжная надстройка `book/` разработана как самостоятельная реализация. При проектировании учитывались общие архитектурные идеи open-source систем для длинной художественной прозы, включая:

- `iLearn-Lab/NovelClaw` — chapter-oriented workflow, storyboards, character/world views и memory-aware writing control; репозиторий распространяется по MIT License;
- `nonever2109/novel_writer_agent` — многоэтапная обработка главы и story-memory workflow; исходный код из него не копировался, поскольку в корне репозитория не была обнаружена отдельная лицензия;
- `Deng-m1/MaliangAINovalWriter` — иерархия произведение → том → глава → сцена и систематизация worldbuilding; проект распространяется по Apache License 2.0;
- `THUDM/LongWriter` — идея plan-then-write для длинного текста;
- `jaaack-wang/llms-implicit-writing-styles-imitation` — исследовательские подходы к анализу референсного стиля.

В `book/` не включались прямые копии исходного кода этих систем. Реализованы собственные Markdown/YAML-шаблоны и инструкции, совместимые с форматом skill-пакета.

Эта сборка не является официальным продолжением или одобренной версией перечисленных проектов.
