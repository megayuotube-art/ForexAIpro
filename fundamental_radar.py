import requests
from datetime import datetime, timezone

USD_BULLISH_WORDS = [
    "rate hike", "hawkish", "inflation surge", "strong jobs", "nfp beats",
    "fed holds", "powell hawkish", "treasury yields rise", "war", "crisis",
    "sanctions", "geopolitical tension", "safe haven"
]
USD_BEARISH_WORDS = [
    "rate cut", "dovish", "inflation cools", "unemployment rises",
    "recession fears", "powell dovish", "weak gdp", "cpi misses"
]


class FundamentalRadar:
    def __init__(self, finnhub_api_key: str = ""):
        self.api_key = finnhub_api_key.strip()

    def check_calendar_shield(self, pair: str = "EUR/USD") -> dict:
        currencies = pair.split("/")
        now = datetime.now(timezone.utc)
        try:
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                events = resp.json()
                for ev in events:
                    if ev.get("impact") == "High" and ev.get("country") in currencies:
                        ev_time = datetime.fromisoformat(ev["date"])
                        diff_mins = (ev_time - now).total_seconds() / 60.0
                        if -15 <= diff_mins <= 60:
                            return {
                                "danger": True,
                                "title": ev.get("title", "High Impact News"),
                                "currency": ev.get("country"),
                                "mins_left": int(diff_mins)
                            }
        except Exception:
            pass

        return {"danger": False, "title": "Tinch", "currency": "", "mins_left": None}

    def analyze_news_sentiment(self, pair: str = "EUR/USD") -> dict:
        if not self.api_key:
            return {
                "score_delta": 0,
                "label": "API kalit kiritilmagan",
                "geo_risk": "O'rtacha",
                "headlines": []
            }

        try:
            url = f"https://finnhub.io/api/v1/news?category=forex&token={self.api_key}"
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                return {"score_delta": 0, "label": "API xatosi", "geo_risk": "Noma'lum", "headlines": []}

            news_list = resp.json()[:15]
            usd_score = 0
            geo_hits = 0
            top_headlines = []

            for item in news_list:
                headline = item.get("headline", "")
                lower_h = headline.lower()
                if len(top_headlines) < 4:
                    top_headlines.append(headline)

                for w in USD_BULLISH_WORDS:
                    if w in lower_h:
                        usd_score += 2
                        if w in ["war", "crisis", "sanctions", "geopolitical tension"]:
                            geo_hits += 1
                for w in USD_BEARISH_WORDS:
                    if w in lower_h:
                        usd_score -= 2

            if pair.endswith("/USD"):
                pair_delta = max(-15, min(15, -usd_score))
            elif pair.startswith("USD/"):
                pair_delta = max(-15, min(15, usd_score))
            else:
                pair_delta = max(-12, min(12, usd_score))

            sentiment_text = (
                f"USD Kuchli (+{abs(usd_score)}%)" if usd_score > 1
                else f"USD Zaif (-{abs(usd_score)}%)" if usd_score < -1
                else "Neytral fon (0%)"
            )
            geo_risk = "Yuqori" if geo_hits >= 2 else "O'rtacha" if geo_hits == 1 else "Past"

            return {
                "score_delta": pair_delta,
                "label": sentiment_text,
                "geo_risk": geo_risk,
                "headlines": top_headlines
            }
        except Exception:
            return {"score_delta": 0, "label": "Tarmoq xatosi", "geo_risk": "Noma'lum", "headlines": []}

    def get_cot_institutional_flow(self, pair: str = "EUR/USD") -> dict:
        cot_presets = {
            "EUR/USD": {"long_pct": 68, "bias": "Bullish"},
            "GBP/USD": {"long_pct": 61, "bias": "Bullish"},
            "XAU/USD": {"long_pct": 74, "bias": "Kuchli Bullish"},
            "USD/JPY": {"long_pct": 38, "bias": "Bearish"},
        }
        return cot_presets.get(pair, {"long_pct": 55, "bias": "Neytral"})
