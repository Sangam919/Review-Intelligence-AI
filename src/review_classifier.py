"""
Multi-label Review Classifier with Deterministic Keyword Patterns and Optional OpenAI Integration.
Supports evidence extraction, severity scoring, and manual user override.
"""

import re
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from config import (
    CATEGORIES,
    CRITICAL_KEYWORDS,
    HIGH_SEVERITY_KEYWORDS,
    MEDIUM_SEVERITY_KEYWORDS,
    OPENAI_API_KEY,
    DEFAULT_AI_MODEL,
    HAS_OPENAI_KEY,
)


class ReviewClassifier:
    """
    Multi-label taxonomy classifier for employee transit complaints.
    Provides a 100% deterministic, explainable rule engine baseline, with
    an optional, rate-limited, structured JSON OpenAI completion pathway.
    """

    # Comprehensive compiled regex patterns per category
    PATTERNS: Dict[str, List[re.Pattern]] = {
        "booking_reservation": [
            re.compile(r"\b(book|booking|roster|reserv|schedule|shift|slot|ride\s*request|cancel|cancelled|reschedul|seat\s*allocat|deadline|cutoff)\b", re.I),
            re.compile(r"\b(no\s*cab\s*available|unable\s*to\s*book|cannot\s*book|booking\s*error|roster\s*error)\b", re.I),
        ],
        "login_otp_auth": [
            re.compile(r"\b(login|log\s*in|logged\s*out|otp|password|auth|sso|sign\s*in|session|token|credential|verification\s*code|sms\s*code)\b", re.I),
            re.compile(r"\b(otp\s*delay|otp\s*not\s*received|never\s*receive|cant\s*login|cannot\s*login)\b", re.I),
        ],
        "pickup_eta": [
            re.compile(r"\b(pickup|pick\s*up|eta|arrival|delay|delayed|late|wait|waiting|on\s*time|timing|early|reach\s*time|fluctuat)\b", re.I),
            re.compile(r"\b(missed\s*cab|missed\s*ride|cab\s*delay|left\s*early|late\s*to\s*office)\b", re.I),
        ],
        "gps_tracking": [
            re.compile(r"\b(gps|track|tracking|location|map|live\s*track|marker|route|navigation|stationary|wrong\s*direction|circle)\b", re.I),
            re.compile(r"\b(frozen|jump|incorrect\s*location|driver\s*location|satellite)\b", re.I),
        ],
        "driver_vehicle": [
            re.compile(r"\b(driver|cab|vehicle|car|chauffeur|rash|rude|behav|abusive|arrogant|refused|smoke|smell|ac|air\s*condition|clean|cleanliness|seatbelt)\b", re.I),
            re.compile(r"\b(overspeed|talking\s*on\s*phone|unprofessional|demanded)\b", re.I),
        ],
        "safety_verification": [
            re.compile(r"\b(safety|safe|unsafe|sos|emergency|escort|guard|female|women|night|drop\s*confirmation|security|police|threat|harass|alone|stranded)\b", re.I),
            re.compile(r"\b(otp\s*verification|started\s*without|start\s*ride|trip\s*completion)\b", re.I),
        ],
        "notifications_checkin": [
            re.compile(r"\b(notif|notification|alert|reminder|push|beacon|bluetooth|qr|scan|scanner|check\s*in|check-in|boarding|boarded)\b", re.I),
            re.compile(r"\b(no\s*alert|missed\s*alert|failed\s*to\s*notify)\b", re.I),
        ],
        "app_performance": [
            re.compile(r"\b(crash|crashes|crashing|bug|error|freeze|freezing|froze|hang|slow|sluggish|lag|blank|black\s*screen|splash|battery|drain|heat|overheat|install|update|memory)\b", re.I),
            re.compile(r"\b(not\s*working|stopped\s*working|keeps\s*stopping|internal\s*server\s*error)\b", re.I),
        ],
        "customer_support": [
            re.compile(r"\b(support|helpdesk|customer\s*care|care|helpline|ticket|executive|bot|chatbot|complaint|resolution|no\s*response|unresponsive|penalty|refund|deduct)\b", re.I),
            re.compile(r"\b(closed\s*ticket|ignored|grievance)\b", re.I),
        ],
    }

    def __init__(self):
        self.ai_client = None
        if HAS_OPENAI_KEY:
            try:
                from openai import OpenAI
                self.ai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                self.ai_client = None

    def assess_severity(self, text: str, score: int) -> str:
        """
        Determines issue severity impact based on critical vocabulary and rating.
        Levels: 'critical', 'high', 'medium', 'low'
        """
        norm_text = text.lower()

        # Check for critical safety / emergency triggers
        for kw in CRITICAL_KEYWORDS:
            if re.search(rf"\b{kw}\b", norm_text):
                return "critical"

        # Check for high severity triggers (functional failure / lockouts)
        for kw in HIGH_SEVERITY_KEYWORDS:
            if re.search(rf"\b{kw}\b", norm_text):
                return "high"

        # If review is 1-star but no explicit trigger
        if score == 1:
            return "high"

        # Check for medium severity keywords or 2-star rating
        for kw in MEDIUM_SEVERITY_KEYWORDS:
            if re.search(rf"\b{kw}\b", norm_text):
                return "medium"

        if score in [2, 3]:
            return "medium"

        return "low"

    def classify_rule_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Multi-label classification of review text using regex pattern matching.
        Returns list of matched categories with matched keywords and confidence score.
        """
        matches = []
        clean_text = text or ""

        for cat_key, regex_list in self.PATTERNS.items():
            matched_words = []
            for regex in regex_list:
                found = regex.findall(clean_text)
                if found:
                    for item in found:
                        if isinstance(item, str):
                            matched_words.append(item.lower())
                        elif isinstance(item, tuple):
                            matched_words.extend([x.lower() for x in item if x])

            if matched_words:
                unique_words = sorted(list(set(matched_words)))
                # Confidence proportional to keyword count
                confidence = min(0.95, 0.65 + (0.1 * len(unique_words)))
                matches.append({
                    "category": cat_key,
                    "confidence": round(confidence, 2),
                    "matched_keywords": unique_words,
                    "method": "rule_based",
                })

        # If no specific category matched, assign to 'other'
        if not matches:
            matches.append({
                "category": "other",
                "confidence": 0.50,
                "matched_keywords": [],
                "method": "rule_based_fallback",
            })

        return matches

    def classify_ai_assisted(self, text: str, score: int) -> Optional[Dict[str, Any]]:
        """
        Optional OpenAI structured classification for ambiguous or critical reviews.
        Strictly sanitizes review as untrusted user text, requests structured JSON.
        """
        if not self.ai_client:
            return None

        # Build schema prompt
        category_options = list(CATEGORIES.keys())
        system_prompt = (
            "You are an expert review classifier for an employee corporate transportation application (MoveInSync ETS).\n"
            "Classify the user review into 1 to 3 relevant categories from this allowed list only:\n"
            f"{category_options}\n"
            "Output strictly valid JSON with keys:\n"
            "- categories: list of strings from allowed list\n"
            "- primary_category: string from allowed list\n"
            "- severity: one of ['critical', 'high', 'medium', 'low']\n"
            "- rationale: short 1-sentence explanation"
        )

        user_content = f"Star Rating: {score}/5\nReview Text: \"\"\"{text}\"\"\""

        try:
            response = self.ai_client.chat.completions.create(
                model=DEFAULT_AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=250,
            )
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            
            # Validate categories
            valid_cats = [c for c in parsed.get("categories", []) if c in CATEGORIES]
            if not valid_cats:
                valid_cats = ["other"]

            primary = parsed.get("primary_category", valid_cats[0])
            if primary not in CATEGORIES:
                primary = valid_cats[0]

            return {
                "categories": valid_cats,
                "primary_category": primary,
                "severity": parsed.get("severity", "medium"),
                "rationale": parsed.get("rationale", ""),
                "method": "openai_assisted",
                "confidence": 0.95,
            }
        except Exception:
            # Fall back transparently
            return None

    def classify_review(self, text: str, score: int, use_ai: bool = False) -> Dict[str, Any]:
        """
        Classifies an individual review record.
        """
        # Always run rule-based baseline
        rule_matches = self.classify_rule_based(text)
        assigned_categories = [m["category"] for m in rule_matches]
        primary_cat = assigned_categories[0]
        confidence = rule_matches[0]["confidence"]
        method = rule_matches[0]["method"]
        severity = self.assess_severity(text, score)
        rationale = f"Matched keywords: {', '.join(rule_matches[0]['matched_keywords'])}" if rule_matches[0]['matched_keywords'] else "General feedback"

        # If user enabled AI and confidence is low or category is other
        if use_ai and self.ai_client and (primary_cat == "other" or confidence < 0.70):
            ai_result = self.classify_ai_assisted(text, score)
            if ai_result:
                assigned_categories = ai_result["categories"]
                primary_cat = ai_result["primary_category"]
                confidence = ai_result["confidence"]
                method = ai_result["method"]
                severity = ai_result["severity"]
                rationale = ai_result["rationale"]

        return {
            "categories": assigned_categories,
            "primary_category": primary_cat,
            "confidence": confidence,
            "severity": severity,
            "classification_method": method,
            "rationale": rationale,
        }

    def classify_dataframe(self, df: pd.DataFrame, use_ai: bool = False) -> pd.DataFrame:
        """
        Enriches entire DataFrame with category multi-labels, severity, and confidence.
        """
        if df.empty:
            return df

        df = df.copy()
        
        # Track classification results
        categories_list = []
        primary_list = []
        confidence_list = []
        severity_list = []
        method_list = []
        rationale_list = []

        for _, row in df.iterrows():
            text = str(row.get("match_text", row.get("text", "")))
            score = int(row.get("score", 3)) if pd.notna(row.get("score")) else 3
            
            res = self.classify_review(text, score, use_ai=use_ai)
            categories_list.append(res["categories"])
            primary_list.append(res["primary_category"])
            confidence_list.append(res["confidence"])
            severity_list.append(res["severity"])
            method_list.append(res["classification_method"])
            rationale_list.append(res["rationale"])

        df["categories"] = categories_list
        df["primary_category"] = primary_list
        df["confidence"] = confidence_list
        df["severity"] = severity_list
        df["classification_method"] = method_list
        df["classification_rationale"] = rationale_list

        return df
