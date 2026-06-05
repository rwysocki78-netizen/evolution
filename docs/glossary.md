# Evolution — Glossary (EN ↔ PL)

Code and documentation are in **English**. This table gives the **Polish** terms to
use when presenting the project, so identifiers stay clean while explanations can
be given in Polish.

The convention: keep the English identifier in code, use the Polish term as a
label/explanation when speaking or in a Polish-language UI.

---

## Core concepts

| English (code/docs) | Polish (presentation) | Note |
|---------------------|-----------------------|------|
| Creature | Stworzenie / Stworzenia (pl.) | The species |
| Board / Grid | Plansza / Siatka | |
| Cell | Komórka / Pole | |
| Tick / Turn | Tura / Krok | Discrete time step |
| Wall (hard wall) | Ściana / Twarda granica | Impassable edge |
| Simulation | Symulacja | |
| Population | Populacja | |
| Generation | Pokolenie | |
| Evolution | Ewolucja | |
| Natural selection | Dobór naturalny | |

## Creature state

| English | Polish | Note |
|---------|--------|------|
| Sex (male / female) | Płeć (samiec / samica) | |
| Energy | Energia | Doubles as health |
| Age | Wiek | In ticks |
| Position | Pozycja | |
| Vision range | Zasięg wzroku | |
| Genome | Genom | |
| Gene / Trait | Gen / Cecha | |

## Genes

| English | Polish |
|---------|--------|
| Lifespan | Długość życia |
| Vision range | Zasięg wzroku |
| Hunger threshold | Próg głodu |
| Safe threshold | Próg bezpieczeństwa |
| Metabolism | Metabolizm |
| Aggression | Agresja |
| Poison resistance | Odporność na truciznę |

## Mechanics

| English | Polish | Note |
|---------|--------|------|
| Move | Ruch / Poruszanie się | |
| Fight | Walka | Same-sex encounter |
| Reproduction | Rozmnażanie | Opposite-sex encounter |
| Offspring / Litter | Potomstwo / Miot | |
| Inheritance | Dziedziczenie | |
| Darwinian inheritance | Dziedziczenie darwinowskie | Only inherited baseline passes on |
| Lamarckian inheritance | Dziedziczenie lamarckowskie | Acquired traits pass on (deferred to later version) |
| Maturity age | Wiek dojrzałości | Min age to reproduce |
| Juvenile | Osobnik młodociany / niedojrzały | `age < MATURITY_AGE` |
| Maximum energy | Maksymalna energia | Global energy ceiling |
| Mutation | Mutacja | |
| Mutation rate | Współczynnik mutacji | |
| Death by old age | Śmierć ze starości | |
| Death by starvation | Śmierć z głodu | |
| Death in a fight | Śmierć w walce | |

## World objects

| English | Polish |
|---------|--------|
| Fruit | Owoc / Owoce (pl.) |
| Poison | Trucizna |
| Respawn | Odradzanie / Pojawianie się na nowo |

## Behaviour

| English | Polish | Note |
|---------|--------|------|
| Behaviour strategy | Strategia zachowania | The pluggable decision model |
| Threshold (strategy) | Progowa (strategia) | Decisions from energy thresholds |
| Priority (strategy) | Priorytetowa (strategia) | Fixed ordered priority list |
| Decision | Decyzja | |

## Statistics

| English | Polish |
|---------|--------|
| Statistics | Statystyki |
| Average energy | Średnia energia |
| Births | Narodziny |
| Deaths | Zgony / Śmierci |
| Trait drift | Dryf cech |
| Snapshot | Migawka / Zrzut stanu |
| Run (a simulation run) | Przebieg (symulacji) |

## Technical (usually left in English, given here for completeness)

| English | Polish |
|---------|--------|
| Backend | Część serwerowa / Backend |
| Frontend | Część kliencka / Frontend |
| Database | Baza danych |
| Schema | Schemat |
| Parameter | Parametr |
| Seed (RNG) | Ziarno (generatora losowego) |

---

> Tip for the presentation: introduce the species once as
> *"Creatures (Stworzenia)"* and the key term *"genome (genom)"*, then you can
> move fluidly between the code (English) and the explanation (Polish) without
> confusing the audience.
