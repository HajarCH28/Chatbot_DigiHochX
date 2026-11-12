"""
Wissenschaftliche und Konversationelle Intent-Erkennung für DigiHochX.
Unterscheidet zuverlässig zwischen Alltagsdialog (ohne RAG-Retrieval)
und wissenschaftlichen Rechercheanfragen (mit RAG-Retrieval).
"""

import re
from enum import Enum
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field


class UserIntent(str, Enum):
    GREETING = "greeting"
    ACKNOWLEDGEMENT = "acknowledgement"
    FAREWELL = "farewell"
    IDENTITY_OR_CAPABILITIES = "identity_or_capabilities"
    LANGUAGE_REQUEST = "language_request"
    SIMPLIFICATION_REQUEST = "simplification_request"
    GENERAL_CONVERSATION = "general_conversation"
    SCIENTIFIC_QUESTION = "scientific_question"
    DOCUMENT_ANALYSIS = "document_analysis"
    RESEARCH_AGENDA_REQUEST = "research_agenda_request"
    AMBIGUOUS_CLARIFICATION = "ambiguous_clarification"


class IntentResult(BaseModel):
    """Ergebnis der semantischen Intent-Klassifikation."""
    intent: UserIntent
    is_conversational: bool = Field(
        description="True, wenn die Anfrage rein dialogisch ist und KEIN RAG-Retrieval benötigt wird"
    )
    detected_language: str = Field(default="de", description="Erkannte Sprache der Anfrage ('de' oder 'en')")
    requested_language: Optional[str] = Field(
        default=None, description="Explizit angeforderte Zielsprache, falls vorhanden"
    )
    analysis_mode: str = Field(
        default="general",
        description="RAG-Analysemodus (classification, interdisciplinary, tension_analysis, research_gaps, research_questions, research_agenda)"
    )
    confidence: float = Field(default=1.0)


class IntentClassifier:
    """Leichtgewichtiger, deterministischer und robuster Intent-Klassifikator."""

    # Wissenschaftliche Kernautoren und Konzepte des DigiHochX-Korpus
    SCIENTIFIC_AUTHORS = [
        "russ", "sieber", "weber", "leikert", "tintore", "tintoré",
        "arbo", "arbós", "elbawab", "knackstedt", "cameron", "quinn"
    ]

    SCIENTIFIC_TERMS = [
        "organisationskultur", "organizational culture", "business-it-alignment", "bita",
        "safe", "scaled agile", "reifegrad", "stage of growth", "learning capacity",
        "lernkapazität", "organisationales lernen", "organizational learning", "lernkultur",
        "learning culture", "dloq", "information acquisition", "knowledge dissemination",
        "hochschulleistung", "university performance", "sustainable performance",
        "competing values", "clan-kultur", "hierarchiekultur", "marktkultur", "adhokratie",
        "schnittstelle", "schnittstellenprozess", "interface", "verwaltung", "forschung",
        "lehre", "hochschulentwicklung", "governance", "it-governance", "barrieren",
        "barriers to learning", "prozessmodellierung", "prozessmanagement",
        "wirtschaftsinformatik", "organisationspädagogik", "business information systems",
        "organizational pedagogy", "deskriptiv", "descriptive", "präskriptiv", "prescriptive",
        "forschungsagenda", "research agenda", "forschungslücke", "research gap",
        "forschungsfrage", "research question", "zhaw", "fallstudie", "case study",
        "empirisch", "empirical", "korpus", "corpus", "artefakt", "gestaltungsvorschlag"
    ]

    # Reguläre Ausdrücke für Alltagsdialoge
    RE_GREETING_DE = re.compile(
        r"^(hallo|hi|hey|moin(\s+moin)?|guten\s+(morgen|tag|abend)|servus|grüß\s+(gott|dich)|hallo\s+zusammen)[\s!.,?:;]*$",
        re.IGNORECASE
    )
    RE_GREETING_EN = re.compile(
        r"^(hello|hi|hey|good\s+(morning|afternoon|evening)|howdy|greetings)[\s!.,?:;]*$",
        re.IGNORECASE
    )

    RE_THANKS_DE = re.compile(
        r"^(danke(\s+dir|\s+ihnen|\s+sehr|\s+schön)?|vielen\s+dank|dankeschön|herzlichen\s+dank|besten\s+dank|super,?\s*danke|alles\s+klar,?\s*danke|perfekt,?\s*danke)[\s!.,?:;]*$",
        re.IGNORECASE
    )
    RE_THANKS_EN = re.compile(
        r"^(thank\s+you(\s+so\s+much|\s+very\s+much)?|thanks(\s+a\s+lot)?|many\s+thanks|thx|great,?\s*thanks|got\s+it,?\s*thanks|appreciate\s+it)[\s!.,?:;]*$",
        re.IGNORECASE
    )

    RE_FAREWELL_DE = re.compile(
        r"^(tschüss|auf\s+wiedersehen|bis\s+(später|bald|morgen)|schönen\s+tag(\s+noch)?|schönes\s+wochenende|ciao|gute\s+nacht)[\s!.,?:;]*$",
        re.IGNORECASE
    )
    RE_FAREWELL_EN = re.compile(
        r"^(bye|goodbye|bye\s+bye|see\s+you(\s+later|\s+soon)?|have\s+a\s+(nice|great)\s+day|farewell|good\s+night)[\s!.,?:;]*$",
        re.IGNORECASE
    )

    RE_IDENTITY_DE = re.compile(
        r"(wer\s+bist\s+du|was\s+bist\s+du|wie\s+heißt\s+du|stell\s+dich\s+vor|wer\s+hat\s+dich|über\s+dich|was\s+ist\s+digihochx)",
        re.IGNORECASE
    )
    RE_IDENTITY_EN = re.compile(
        r"(who\s+are\s+you|what\s+are\s+you|what\s+is\s+your\s+name|introduce\s+yourself|tell\s+me\s+about\s+yourself|who\s+created\s+you|what\s+is\s+digihochx)",
        re.IGNORECASE
    )

    RE_CAPABILITIES_DE = re.compile(
        r"(was\s+kannst\s+du|was\s+sind\s+deine\s+fähigkeiten|wie\s+kannst\s+du\s+(mir\s+)?helfen|wofür\s+bist\s+du\s+da|welche\s+funktionen\s+hast\s+du|was\s+machst\s+du)",
        re.IGNORECASE
    )
    RE_CAPABILITIES_EN = re.compile(
        r"(what\s+can\s+you\s+do|how\s+can\s+you\s+help|what\s+are\s+your\s+capabilities|what\s+do\s+you\s+do|what\s+is\s+your\s+purpose)",
        re.IGNORECASE
    )

    RE_LANG_TO_EN = re.compile(
        r"(auf\s+englisch|in\s+english|speak\s+english|can\s+you\s+(answer|speak|reply)\s+in\s+english|please\s+(answer|reply|speak)\s+in\s+english|antworte\s+(bitte\s+)?auf\s+englisch|kannst\s+du\s+auf\s+englisch)",
        re.IGNORECASE
    )
    RE_LANG_TO_DE = re.compile(
        r"(auf\s+deutsch|in\s+german|speak\s+german|can\s+you\s+(answer|speak|reply)\s+in\s+german|please\s+(answer|reply|speak)\s+in\s+german|antworte\s+(bitte\s+)?auf\s+deutsch|kannst\s+du\s+auf\s+deutsch)",
        re.IGNORECASE
    )

    RE_SIMPLIFY_DE = re.compile(
        r"(einfacher\s+erklären|einfacher\s+erlaeutern|in\s+einfachen\s+worten|nicht\s+so\s+kompliziert|leichter\s+verständlich|erkläre\s+mir\s+diesen\s+begriff\s+einfacher|begriff\s+einfacher)",
        re.IGNORECASE
    )
    RE_SIMPLIFY_EN = re.compile(
        r"(explain\s+(this\s+)?(more\s+)?simply|simplify|in\s+simple\s+terms|explain\s+like\s+i(\s*a)?m\s+5|in\s+plain\s+english)",
        re.IGNORECASE
    )

    @classmethod
    def _detect_language(cls, text: str) -> str:
        """Erkennt anhand typischer Signalwörter, ob der Text eher Deutsch oder Englisch ist."""
        lower = text.lower()
        german_indicators = [" der ", " die ", " das ", " und ", " ist ", " wie ", " was ", " welche ", " welcher ", " bitte ", " danke ", " guten "]
        english_indicators = [" the ", " and ", " is ", " what ", " which ", " how ", " please ", " thanks ", " good "]

        padded = f" {lower} "
        de_score = sum(1 for ind in german_indicators if ind in padded)
        en_score = sum(1 for ind in english_indicators if ind in padded)

        if en_score > de_score:
            return "en"
        return "de"

    @classmethod
    def _has_scientific_signals(cls, text: str) -> bool:
        """Prüft, ob der Text konkrete Autorennamen oder wissenschaftliche Fachbegriffe enthält."""
        lower = text.lower()
        # Prüfen auf Autoren
        for author in cls.SCIENTIFIC_AUTHORS:
            if re.search(rf"\b{author}\b", lower):
                return True
        # Prüfen auf Fachbegriffe
        for term in cls.SCIENTIFIC_TERMS:
            if term in lower:
                return True
        return False

    @classmethod
    def _determine_analysis_mode(cls, text: str) -> str:
        """Ordnet wissenschaftlichen Anfragen einen passenden DigiHochX-Analysemodus zu."""
        lower = text.lower()
        if "deskriptiv" in lower or "präskriptiv" in lower or "descriptive" in lower or "prescriptive" in lower:
            return "classification"
        elif ("wirtschaftsinformatik" in lower and "organisationspädagogik" in lower) or "vergleich" in lower or "interdisziplinär" in lower or "compare" in lower:
            return "interdisciplinary"
        elif "konflikt" in lower or "spannung" in lower or "tension" in lower or "conflict" in lower or "schnittstelle" in lower or "interface" in lower:
            return "tension_analysis"
        elif "lücke" in lower or "luecke" in lower or "gap" in lower:
            return "research_gaps"
        elif "forschungsfrage" in lower or "research question" in lower:
            return "research_questions"
        elif "forschungsagenda" in lower or "research agenda" in lower or "agenda" in lower:
            return "research_agenda"
        return "general"

    @classmethod
    def classify(cls, query: str, current_language: str = "de") -> IntentResult:
        """Klassifiziert den Intent des Nutzers präzise und entscheidet über RAG-Aktivierung."""
        clean = query.strip()
        lower = clean.lower()
        detected_lang = cls._detect_language(clean)

        # 1. Sprachwechsel-Anfragen erkennen
        if cls.RE_LANG_TO_EN.search(lower):
            return IntentResult(
                intent=UserIntent.LANGUAGE_REQUEST,
                is_conversational=True,
                detected_language="en",
                requested_language="en",
                confidence=1.0
            )
        if cls.RE_LANG_TO_DE.search(lower):
            return IntentResult(
                intent=UserIntent.LANGUAGE_REQUEST,
                is_conversational=True,
                detected_language="de",
                requested_language="de",
                confidence=1.0
            )

        # 2. Prüfen, ob die Nachricht wissenschaftliche Kernsignale enthält
        # Wenn wissenschaftliche Signale vorhanden sind, wird IMMER RAG aktiviert,
        # selbst wenn die Nachricht mit einer Höflichkeitsformel ("Hallo, welche...") beginnt.
        has_sci_signal = cls._has_scientific_signals(clean)

        # 3. Reine Begrüßungen (ohne wissenschaftliche Frage)
        if cls.RE_GREETING_DE.match(lower) or cls.RE_GREETING_EN.match(lower):
            return IntentResult(
                intent=UserIntent.GREETING,
                is_conversational=True,
                detected_language=detected_lang,
                confidence=1.0
            )

        # 4. Reine Danksagungen / Bestätigungen
        if cls.RE_THANKS_DE.match(lower) or cls.RE_THANKS_EN.match(lower):
            return IntentResult(
                intent=UserIntent.ACKNOWLEDGEMENT,
                is_conversational=True,
                detected_language=detected_lang,
                confidence=1.0
            )

        # 5. Reine Verabschiedungen
        if cls.RE_FAREWELL_DE.match(lower) or cls.RE_FAREWELL_EN.match(lower):
            return IntentResult(
                intent=UserIntent.FAREWELL,
                is_conversational=True,
                detected_language=detected_lang,
                confidence=1.0
            )

        # 6. Identitäts- oder Funktionsabfragen
        if (cls.RE_IDENTITY_DE.search(lower) or cls.RE_CAPABILITIES_DE.search(lower) or
            cls.RE_IDENTITY_EN.search(lower) or cls.RE_CAPABILITIES_EN.search(lower)) and not has_sci_signal:
            return IntentResult(
                intent=UserIntent.IDENTITY_OR_CAPABILITIES,
                is_conversational=True,
                detected_language=detected_lang,
                confidence=0.95
            )

        # 7. Vereinfachungsanfragen ("Erkläre mir diesen Begriff einfacher")
        if cls.RE_SIMPLIFY_DE.search(lower) or cls.RE_SIMPLIFY_EN.search(lower):
            return IntentResult(
                intent=UserIntent.SIMPLIFICATION_REQUEST,
                is_conversational=True,
                detected_language=detected_lang,
                confidence=0.9
            )

        # 8. Ambivalente oder extrem kurze Eingaben ohne wissenschaftliche Relevanz (z.B. "?", "ok", "cool")
        if len(clean) <= 4 and not has_sci_signal and not clean.isdigit():
            return IntentResult(
                intent=UserIntent.AMBIGUOUS_CLARIFICATION,
                is_conversational=True,
                detected_language=detected_lang,
                confidence=0.8
            )

        # 9. Spezifische wissenschaftliche Modi ermitteln
        mode = cls._determine_analysis_mode(clean)
        intent = UserIntent.SCIENTIFIC_QUESTION
        if mode == "classification":
            intent = UserIntent.DOCUMENT_ANALYSIS
        elif mode == "research_agenda":
            intent = UserIntent.RESEARCH_AGENDA_REQUEST

        return IntentResult(
            intent=intent,
            is_conversational=False,
            detected_language=detected_lang,
            analysis_mode=mode,
            confidence=0.95 if has_sci_signal else 0.8
        )

