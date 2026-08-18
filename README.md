# Nine Eleven — tarcza Wear OS

Tarcza dla **Samsung Galaxy Watch Ultra** (Wear OS 5+ / One UI 6 Watch+),
w **Watch Face Format v2** — deklaratywny XML, zero kodu, mały pakiet, niskie
zużycie baterii.

![podgląd](watchface/src/main/res/drawable-nodpi/preview.png)

| Element | Źródło |
| --- | --- |
| Godzina, 24 h, siedmiosegmentowo | `[HOUR_0_23_Z]` : `[MINUTE_Z]` |
| Data (plakietka) | `[DAY]` |
| Kroki | `[STEP_COUNT]` |
| Temperatura | konfigurowalna komplikacja Samsung Weather |
| Bateria (czerwona poniżej 15 %) | `[BATTERY_PERCENT]` |
| **Energy score** | slot komplikacji — patrz niżej |
| 6 sylwetek aut | `ListConfiguration` |
| 8 zestawów kolorów | `ColorConfiguration` |

---

## Konfiguracja na zegarku

Przytrzymaj tarczę → **Dostosuj**:

* **Kolor** — 8 zestawów. Barwa steruje autem, plakietką daty i wartością
  energii; motyw *Mięta* koloruje dodatkowo zegar.
* **Samochód** — 6 nadwozi: coupé z silnikiem z tyłu, klinowe GT, centralny
  silnik, GT z długą maską, hipersamochód, klasyk lat 60.
* **Temperatura** — dotknij pola `TEMP`. Domyślnie jest ustawiona aplikacja
  Samsung Weather; możesz wybrać temperaturę, temperaturę odczuwalną, UV lub
  innego dostawcę komplikacji.
* **Energy score** — dotknij linii `ENERGIA` i wybierz dostawcę, jeśli jest
  zainstalowany.

Auta to białe sylwetki barwione przez `tintColor`, więc jeden komplet obrazków
obsługuje wszystkie palety.

---

## Energy score — istotne zastrzeżenie

Watch Face Format **nie ma** systemowego źródła danych dla Energy score
Samsung Health. Dostępne źródła zdrowotne to dokładnie `STEP_COUNT`,
`STEP_GOAL`, `STEP_PERCENT`, `HEART_RATE`, `HEART_RATE_Z`
(`tools/wff/xsd/2/common/attributes/sourceType.xsd`). Energy score da się
pokazać wyłącznie przez **komplikację** wystawianą przez Samsung Health.

Linia `ENERGIA` to `ComplicationSlot` obsługujący `SHORT_TEXT`, `RANGED_VALUE`,
`GOAL_PROGRESS` i `EMPTY` — niezależnie od postaci wartości renderuje się
poprawnie. Konfiguracja jednorazowa, w edytorze tarczy.

Na Galaxy Watch Ultra / One UI 8 Samsung Health nie wystawia Energy Score jako
systemowego providera komplikacji. Dlatego sama tarcza nie może go odczytać z
`watchface.xml`, choć slot jest gotowy na `SHORT_TEXT`, `RANGED_VALUE` i
`GOAL_PROGRESS` oraz ma uprawnienie do odbierania danych od zewnętrznego
providera.

Aby pokazać prawdziwy Energy Score, potrzebny jest osobny provider komplikacji
na zegarku i aplikacja towarzysząca na telefonie: telefon czyta
`DataTypes.ENERGY_SCORE` przez Samsung Health Data SDK po zgodzie użytkownika,
a następnie synchronizuje wartość na zegarek. Samsung udostępnia to SDK na
osobnej licencji; lokalne testy wymagają również trybu deweloperskiego Samsung
Health, a dystrybucja — zatwierdzonego partnerstwa.

---

## AOD

Czarne tło, auto jako kontur w kolorze motywu, plakietka daty obrysem, a zegar
na tle wygaszonego pola segmentów `88:88` — czyli tak, jak wygląda prawdziwy
wyświetlacz LCD z podświetlonymi tylko potrzebnymi segmentami. Reszta (pierścień
minutowy, metryki, tło) gaśnie. Zmierzone zużycie pamięci w ambient: 0,8 MB.

---

## Budowanie i instalacja

```bash
./gradlew :watchface:assembleDebug
```

```bash
adb connect <IP-zegarka>:5555
```

```bash
adb install -r watchface/build/outputs/apk/debug/watchface-debug.apk
```

APK ma ~864 kB. Na zegarku włącz wcześniej *Opcje programisty* → *Debugowanie
ADB* → *Debugowanie przez Wi-Fi*.

---

## Weryfikacja

Oba narzędzia z repo [`google/watchface`](https://github.com/google/watchface):

```bash
java -jar tools/wff/wff-validator.jar 2 watchface/src/main/res/raw/watchface.xml
```

```bash
java -jar tools/wff/memory-footprint.jar --watch-face watchface/build/outputs/apk/debug/watchface-debug.apk --ambient-limit-mb 10 --active-limit-mb 100
```

Stan: walidacja schematu **PASS**, budżet pamięci **PASS**.

---

## Grafika

Nic nie jest zdjęciem ani obrysem cudzej grafiki — wszystko rysowane
proceduralnie:

```bash
python3 tools/gen_art.py --sheet
```

**[tools/cars.py](tools/cars.py)** — profile sześciu nadwozi. Każdy budowany
z publikowanych wymiarów: długość, wysokość, rozstaw osi, zwisy, rozmiary opon
oraz wysokości dachu, linii okien, grzbietu błotnika i reflektora. Układ
współrzędnych jest w realnej skali, więc każdą wysokość można odczytać jako
milimetry:

```
mm = height_mm * (1 - y / height)
```

Komentarze przy punktach podają te milimetry, więc rysunek da się sprawdzić.
Opony przód/tył mają osobne rozmiary — ustawienie „staggered" mocno wpływa na
to, jak sylwetka czyta się z profilu. Szyby, słupek B i linie podziału drzwi są
wyprowadzane z krzywej dachu, więc zawsze do niej pasują.

Detale wycinane w sylwetce: szyby, słupek B, klamka, wloty boczne, listwa
tylnych świateł, wlot przedni, wydech, linia progu, reflektor. Dodawane:
lusterko, skrzydło tylne (auta, które je mają), felga z pięcioma podwójnymi
ramionami i piastą centralną.

**[tools/gen_art.py](tools/gen_art.py)** — rasteryzacja (4× nadpróbkowanie,
Lanczos), pierścień minutowy, tło, podgląd, arkusz kontrolny aut.

### Strojenie

```python
SQUASH   = 0.90              # świadome spłaszczenie - ortograficzne proporcje
                             # czytają się przysadziście w skali zegarka
CAR_BOX  = (54, 134, 372, 106)
TIME_Y, TIME_SIZE = 304, 78
```

Po zmianie: `python3 tools/gen_art.py`, potem `./gradlew :watchface:assembleDebug`.

Ilustracje są własne i **nie zawierają** logotypu, emblematu, nazwy ani
oznaczeń żadnego producenta.

---

## Układ

Przestrzeń projektowa 480×480 — natywna rozdzielczość Ultra.

```
 y  44.. 71   plakietka daty
 y  74..108   energy score
 y 134..240   auto
 y 248        linia
 y 256..291   KROKI | TEMP | BATERIA
 y 304..382   godzina 24 h
```

Pozycje omijają cyfry pierścienia: znaczniki 10 i 50 leżą na y=135, a 20 i 40
na x=62 i x=417.

## Czcionki

* [Saira Condensed](https://fonts.google.com/specimen/Saira+Condensed) — SIL OFL 1.1
* [DSEG7 Classic](https://github.com/keshikan/DSEG) — SIL OFL 1.1

Licencje w `licenses/`.
