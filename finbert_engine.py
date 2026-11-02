"""
FinBERT Engine - Financial NLP Sentiment Analysis forced on CPU
Model: ProsusAI/finbert (HuggingFace)
Outputs: Positive, Negative, Neutral probabilities and trading signal generation
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import Dict, List, Any, Optional
import config

class FinBERTEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FinBERTEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = config.MODEL_NAME):
        if getattr(self, "_initialized", False):
            return

        print(f"[*] تهيئة محرك FinBERT من HuggingFace ({model_name})...")
        
        # تحديد الجهاز ليصبح CPU يدوياً وفقاً للمطلوب بدقة
        self.device = torch.device(config.FORCE_DEVICE)
        self.model_name = model_name

        try:
            # تحميل الـ Tokenizer والنموذج
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

            # نقل النموذج إلى الـ CPU
            self.model.to(self.device)
            self.model.eval()
            print("يعمل النموذج الآن بكفاءة على الـ CPU!")
            self.is_ready = True
        except Exception as e:
            print(f"[!] خطأ في تحميل النموذج: {e}")
            self.is_ready = False
            self.tokenizer = None
            self.model = None

        # خريطة الفئات الخاصة بـ ProsusAI/finbert
        # logits ترتيبها: [positive, negative, neutral]
        self.labels = ["Positive", "Negative", "Neutral"]
        self._cache = {}
        self._initialized = True

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        تحليل نص مالي واحد واستخراج درجات المشاعر (Positive, Negative, Neutral)
        """
        if not text or not text.strip():
            return {
                "sentiment": "Neutral",
                "scores": {"Positive": 0.33, "Negative": 0.33, "Neutral": 0.34},
                "confidence": 0.34,
                "text": ""
            }

        cleaned_text = text.strip()
        if cleaned_text in self._cache:
            return self._cache[cleaned_text]

        if not self.is_ready or self.model is None or self.tokenizer is None:
            # Simple keyword-based safety fallback if model offline
            return self._fallback_analyze(cleaned_text)

        try:
            inputs = self.tokenizer(
                cleaned_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].cpu().tolist()

            scores = {
                "Positive": round(float(probabilities[0]), 4),
                "Negative": round(float(probabilities[1]), 4),
                "Neutral": round(float(probabilities[2]), 4)
            }

            # الفئة ذات أعلى احتمال
            max_label = max(scores, key=scores.get)
            confidence = scores[max_label]

            result = {
                "sentiment": max_label,
                "scores": scores,
                "confidence": confidence,
                "text": cleaned_text
            }

            # Cache up to 1000 items
            if len(self._cache) < 1000:
                self._cache[cleaned_text] = result

            return result

        except Exception as e:
            print(f"[!] خطأ في تشغيل FinBERT على النص: {e}")
            return self._fallback_analyze(cleaned_text)

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        تحليل قائمة من النصوص المالية دفعة واحدة على الـ CPU
        """
        if not texts:
            return []

        results = []
        uncached_indices = []
        uncached_texts = []

        for idx, t in enumerate(texts):
            clean = t.strip() if t else ""
            if not clean:
                results.append(self.analyze_text(""))
            elif clean in self._cache:
                results.append(self._cache[clean])
            else:
                results.append(None)
                uncached_indices.append(idx)
                uncached_texts.append(clean)

        if not uncached_texts:
            return results

        if not self.is_ready or self.model is None or self.tokenizer is None:
            for idx, text in zip(uncached_indices, uncached_texts):
                results[idx] = self._fallback_analyze(text)
            return results

        try:
            inputs = self.tokenizer(
                uncached_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs_batch = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().tolist()

            for i, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                probs = probs_batch[i]
                scores = {
                    "Positive": round(float(probs[0]), 4),
                    "Negative": round(float(probs[1]), 4),
                    "Neutral": round(float(probs[2]), 4)
                }
                max_label = max(scores, key=scores.get)
                res = {
                    "sentiment": max_label,
                    "scores": scores,
                    "confidence": scores[max_label],
                    "text": text
                }
                results[idx] = res
                if len(self._cache) < 1000:
                    self._cache[text] = res

        except Exception as e:
            print(f"[!] خطأ أثناء تحليل المجموعة بـ FinBERT: {e}")
            for idx, text in zip(uncached_indices, uncached_texts):
                results[idx] = self._fallback_analyze(text)

        return results

    def aggregate_pair_sentiment(self, news_items: List[Dict[str, Any]], pair: str) -> Dict[str, Any]:
        """
        تجميع وتحليل مشاعر الأخبار المتعلقة بزوج معين مثل EURUSD
        واستخراج إشارة تداول (BUY / SELL / HOLD) مع نسبة الثقة
        """
        base = pair[:3].upper() if len(pair) >= 6 else pair.upper()
        quote = pair[3:6].upper() if len(pair) >= 6 else "USD"

        # الكلمات المفتاحية المتعلقة بالعملة الأساس والمقابلة
        keywords_base = self._get_currency_keywords(base)
        keywords_quote = self._get_currency_keywords(quote)

        relevant_base = []
        relevant_quote = []

        for item in news_items:
            headline = (item.get("headline") or item.get("text") or item.get("title") or "").lower()
            if not headline:
                continue

            has_base = any(kw.lower() in headline for kw in keywords_base)
            has_quote = any(kw.lower() in headline for kw in keywords_quote)

            if has_base and not has_quote:
                relevant_base.append(item)
            elif has_quote and not has_base:
                relevant_quote.append(item)
            elif has_base and has_quote:
                relevant_base.append(item)
                relevant_quote.append(item)

        # إذا لم نجد أخبار مخصصة بدقة للزوج، نأخذ الأخبار العامة
        if not relevant_base and not relevant_quote and news_items:
            # Use general market sentiment
            relevant_base = news_items[:3]

        texts_base = [x.get("headline") or x.get("text") or x.get("title") for x in relevant_base if x]
        texts_quote = [x.get("headline") or x.get("text") or x.get("title") for x in relevant_quote if x]

        analyses_base = self.analyze_batch(texts_base) if texts_base else []
        analyses_quote = self.analyze_batch(texts_quote) if texts_quote else []

        avg_base_pos = sum(a["scores"]["Positive"] for a in analyses_base) / len(analyses_base) if analyses_base else 0.33
        avg_base_neg = sum(a["scores"]["Negative"] for a in analyses_base) / len(analyses_base) if analyses_base else 0.33

        avg_quote_pos = sum(a["scores"]["Positive"] for a in analyses_quote) / len(analyses_quote) if analyses_quote else 0.33
        avg_quote_neg = sum(a["scores"]["Negative"] for a in analyses_quote) / len(analyses_quote) if analyses_quote else 0.33

        # منطق التداول في أزواج العملات Forex CFDs:
        # إذا كانت مشاعر العملة الأساس إيجابية ومشاعر العملة المقابلة سلبية -> إشارة شراء BUY قوية
        # إذا كانت مشاعر العملة الأساس سلبية ومشاعر العملة المقابلة إيجابية -> إشارة بيع SELL قوية
        bullish_score = (avg_base_pos + avg_quote_neg) / 2.0
        bearish_score = (avg_base_neg + avg_quote_pos) / 2.0
        neutral_score = 1.0 - max(bullish_score, bearish_score)
        if neutral_score < 0:
            neutral_score = 0.05

        scores = {
            "Positive": round(bullish_score, 4),
            "Negative": round(bearish_score, 4),
            "Neutral": round(neutral_score, 4)
        }

        # تحديد إشارة التداول بناءً على عتبة الثقة
        threshold = config.CONFIDENCE_THRESHOLD
        if bullish_score > threshold and bullish_score > bearish_score + 0.10:
            signal = "BUY"
            direction = "شراء (BUY / Long)"
            confidence = bullish_score
        elif bearish_score > threshold and bearish_score > bullish_score + 0.10:
            signal = "SELL"
            direction = "بيع (SELL / Short)"
            confidence = bearish_score
        else:
            signal = "HOLD"
            direction = "ترقب / محايد (HOLD)"
            confidence = max(scores.values())

        return {
            "pair": pair,
            "signal": signal,
            "direction_ar": direction,
            "confidence": round(confidence, 4),
            "scores": scores,
            "base_currency": base,
            "quote_currency": quote,
            "articles_analyzed": len(analyses_base) + len(analyses_quote),
            "sample_headline": (texts_base or texts_quote or ["No recent headlines"])[0]
        }

    def _get_currency_keywords(self, currency: str) -> List[str]:
        mapping = {
            "USD": ["dollar", "usd", "fed", "federal reserve", "powell", "treasury", "united states", "us economy", "cpi", "nfp", "wall street"],
            "EUR": ["euro", "eur", "ecb", "lagarde", "germany", "france", "eurozone", "european", "bundesbank"],
            "GBP": ["pound", "gbp", "sterling", "boe", "bank of england", "bailey", "uk economy", "britain"],
            "JPY": ["yen", "jpy", "boj", "bank of japan", "ueda", "tokyo", "japan"],
            "AUD": ["aussie", "aud", "rba", "reserve bank of australia", "australia", "sydney"],
            "CAD": ["loonie", "cad", "boc", "bank of canada", "macklem", "canada", "oil"],
            "CHF": ["franc", "chf", "snb", "swiss national bank", "switzerland"],
            "NZD": ["kiwi", "nzd", "rbnz", "reserve bank of new zealand", "new zealand"]
        }
        return mapping.get(currency.upper(), [currency.lower()])

    def _fallback_analyze(self, text: str) -> Dict[str, Any]:
        """Safety fallback if model weights are loading or unavailable"""
        lower = text.lower()
        pos_words = ["surge", "gain", "profit", "bull", "growth", "boost", "rally", "positive", "high", "cut interest rate", "cooling inflation"]
        neg_words = ["plunge", "drop", "loss", "bear", "crisis", "decline", "fall", "negative", "recession", "tariff", "war", "escalat", "inflation rise"]

        pos_count = sum(1 for w in pos_words if w in lower)
        neg_count = sum(1 for w in neg_words if w in lower)

        if pos_count > neg_count:
            scores = {"Positive": 0.72, "Negative": 0.15, "Neutral": 0.13}
            max_label = "Positive"
        elif neg_count > pos_count:
            scores = {"Positive": 0.14, "Negative": 0.74, "Neutral": 0.12}
            max_label = "Negative"
        else:
            scores = {"Positive": 0.25, "Negative": 0.25, "Neutral": 0.50}
            max_label = "Neutral"

        return {
            "sentiment": max_label,
            "scores": scores,
            "confidence": scores[max_label],
            "text": text
        }

# Global singleton instance
finbert_engine = FinBERTEngine()

if __name__ == "__main__":
    test_texts = [
        "US inflation slows to 2.4%, boosting expectations of aggressive Federal Reserve rate cuts.",
        "Eurozone manufacturing output collapses unexpectedly as energy costs soar.",
        "Bank of Japan holds interest rates steady and provides no guidance on future hikes."
    ]
    print("\n--- تجربة محرك FinBERT على نصوص مالية ---")
    results = finbert_engine.analyze_batch(test_texts)
    for res in results:
        print(f"\nالنص: {res['text']}")
        print(f"المشاعر: {res['sentiment']} (ثقة: {res['confidence']*100:.1f}%)")
        print(f"الدرجات: {res['scores']}")
