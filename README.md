# Morning Brief Bot

Un bot care iti trimite pe **Telegram**, in fiecare dimineata inainte de London,
un card cu **bias-ul 1H** pe GBPUSD / UK100 / DAX + **stirile high-impact** ale zilei.
Te trezesti, citesti cardul, vanezi entry-uri pe 5M/1M doar in directia data si
eviti ferestrele de news. Gata cu reanalizatul in timpul sesiunii.

Tu nu codezi nimic. Conectezi 2 chestii si dai deploy, fix ca la Recepto.

---

## Ce primesti pe Telegram

```
📊  Morning Brief — Fri 19 Jun

GBPUSD — BIAS: 🟢 LONG
   1H: bullish (HH/HL)
   Draw on liquidity: 1.2945
   Zona OTE (hunt 5M/1M): 1.2760 – 1.2785
   ⏳ pret 1.2820 — asteapta pullback in zona

DAX — BIAS: NEUTRAL
   1H: structura neclara / range - stai pe maini pana se rupe

———
⚠️ High-impact azi (evita ±30 min):
   09:00  GBP  BoE Rate Decision
   15:30  USD  CPI m/m

Structura da directia. Newsul e harta de mine, nu semnal.
```

---

## Setup (~10 min, zero cod)

**1. Pune codul pe GitHub.** Urca folderul asta intr-un repo nou (ex. `morning-brief`).

**2. Fa un bot de Telegram.** In Telegram scrie lui **@BotFather** -> `/newbot` ->
dai un nume -> primesti un **token** (un string lung). Copiaza-l.

**3. Afla chat_id-ul tau.** Scrie lui **@userinfobot** in Telegram -> iti raspunde
cu `Id: 123456789`. Ala e **TELEGRAM_CHAT_ID**. (Apoi da `/start` botului tau nou,
ca sa-ti poata trimite mesaje.)

**4. Deploy pe Railway.** New Project -> Deploy from GitHub repo -> alegi repo-ul.
Railway instaleaza singur tot din `requirements.txt` si porneste `python main.py`.

**5. Pune env vars** (tab Variables in Railway):

| Variabila | Valoare | Obligatoriu |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | token-ul de la BotFather | da |
| `TELEGRAM_CHAT_ID` | id-ul de la userinfobot | da |
| `RUN_AT` | `09:00` (ora locala, inainte de London) | nu |
| `TIMEZONE` | `Europe/Bucharest` | nu |
| `TEST_ON_START` | `true` la prima rulare | nu |

**6. Deploy.** Cu `TEST_ON_START=true` iti trimite **imediat** un card de test,
ca sa verifici ca merge. (Daca schimbi un env var, Railway re-deployeaza —
ca la Recepto, daca nu se prinde forteaza un commit gol.)

**7. Dupa ce vezi cardul,** pune `TEST_ON_START=false`. De-acum trimite o singura
data pe zi, la ora din `RUN_AT`.

---

## Cum schimbi instrumentele sau ora

- **Instrumente:** in `config.py`, dictionarul `INSTRUMENTS`. Numele = ce vrei sa
  apara in card, valoarea = simbolul Yahoo Finance (ex. `EURUSD=X`, `^GDAXI`).
- **Ora:** env var `RUN_AT` (format `HH:MM`).
- **Cat de strict e biasul:** `SWING_STRENGTH` in `config.py` (2 = mai reactiv,
  3 = swinguri mai curate / mai putine semnale).

---

## Cum se calculeaza bias-ul (ca sa ai incredere in el)

Totul e **determinist** — aceleasi candele dau mereu acelasi bias, zero LLM:

1. Gaseste swing highs/lows (pivoti pe 1H).
2. Structura: **bullish** daca face HH+HL, **bearish** daca face LH+LL, altfel **range**.
3. Draw on liquidity = cel mai apropiat pool opus din directia trendului (unde trage pretul).
4. Zona OTE (62%–79% retrace pe leg-ul curent) = unde vanezi entry pe 5M/1M.

In `range` iti zice direct sa stai pe maini.

---

## De stiut

- Pentru indici, Yahoo da **cash index** (^FTSE, ^GDAXI), nu CFD-ul exact al
  broker-ului. Pentru **directie/structura** e ok — se misca la fel. Pentru preturi
  exacte la virgula treci pe un feed de broker (vezi v2).
- Calendarul vine din feed-ul gratuit ForexFactory. Daca o zi nu se incarca,
  cardul tot apare, doar zice "calendar indisponibil — verifica manual".
- Regula de aur, codificata in card: **structura da directia, newsul e filtru de
  volatilitate, nu semnal pe care intri.**
- Asta e un tool de research + disciplina, nu sfat financiar. Bias-ul setat
  dimineata exista ca sa nu mai reanalizezi (si revenge-tradezi) in timpul sesiunii.

---

## Cand vrei v2

- **Feed de broker** (MT5 demo gratis) pentru preturi fix ca la tine.
- **Rules engine pe LTF:** sweep -> MSS pe 5M -> FVG retrace pe 1M, cu alert cand
  setup-ul e valid in directia bias-ului.
- **Risk enforcement:** max 1 trade/zi, stop dupa 2 losses, refuza sub 2R.
- **Auto-journal cu reflection** dupa fiecare trade.
