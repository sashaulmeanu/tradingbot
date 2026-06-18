from datetime import datetime
from config import TZ, NEWS_BUFFER_MIN


def _p(x):
    if x is None:
        return "-"
    return f"{x:.4f}" if abs(x) < 100 else f"{x:,.1f}"


def build_card(biases, events):
    today = datetime.now(TZ).strftime("%a %d %b")
    lines = [f"\U0001F4CA  Morning Brief — {today}", ""]

    for name, b in biases.items():
        if b is None:
            lines.append(f"{name} — date indisponibile")
            lines.append("")
            continue

        if b.direction == "neutral":
            lines.append(f"{name} — BIAS: NEUTRAL")
            lines.append(f"   1H: {b.reason}")
            lines.append("")
            continue

        tag = "\U0001F7E2 LONG" if b.direction == "long" else "\U0001F534 SHORT"
        lines.append(f"{name} — BIAS: {tag}")
        lines.append(f"   1H: {b.reason}")
        if b.draw is not None:
            lines.append(f"   Draw on liquidity: {_p(b.draw)}")
        else:
            lines.append("   Draw: pret la extrem, fara lichiditate clara peste — prudenta")
        lines.append(f"   Zona OTE (hunt 5M/1M): {_p(b.zone_low)} – {_p(b.zone_high)}")
        if b.in_zone:
            lines.append(f"   \u2705 pretul e DEJA in zona ({_p(b.price)})")
        else:
            lines.append(f"   \u23F3 pret {_p(b.price)} — asteapta pullback in zona")
        lines.append("")

    lines.append("———")
    if events is None:
        lines.append("\U0001F4C5 Calendar indisponibil azi — verifica manual ForexFactory.")
    elif not events:
        lines.append("\U0001F4C5 Niciun eveniment high-impact azi. Sesiune curata.")
    else:
        lines.append(f"\u26A0\uFE0F High-impact azi (evita \u00B1{NEWS_BUFFER_MIN} min):")
        for e in events:
            t = e["time"].strftime("%H:%M")
            lines.append(f"   {t}  {e['currency']}  {e['title']}")
    lines.append("")
    lines.append("Structura da directia. Newsul e harta de mine, nu semnal.")
    return "\n".join(lines)
