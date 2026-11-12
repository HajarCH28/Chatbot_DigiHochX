"""
Konversationeller Handler für DigiHochX.
Generiert kontextbewusste, natürliche und präzise Dialogantworten
für Alltagsinteraktionen ohne unnötiges RAG-Retrieval.
"""

import logging
from typing import List, Dict, Optional
from src.core.intent_classifier import IntentResult, UserIntent
from src.llm.gwdg_client import GWDGClient

logger = logging.getLogger(__name__)


class ConversationHandler:
    """Verarbeitet rein dialogische Anfragen mit natürlicher Konversationsintelligenz."""

    RESPONSES = {
        "de": {
            UserIntent.GREETING: (
                "Hallo! Willkommen beim DigiHochX Research Assistant. "
                "Wie kann ich dich heute bei deiner wissenschaftlichen Arbeit unterstützen?"
            ),
            UserIntent.ACKNOWLEDGEMENT: (
                "Sehr gerne! Wenn du weitere Fragen hast oder eine tiefergehende wissenschaftliche "
                "Analyse zu den Dokumenten benötigst, helfe ich dir jederzeit weiter."
            ),
            UserIntent.FAREWELL: (
                "Auf Wiedersehen! Viel Erfolg bei deiner Forschungsarbeit zu DigiHochX. "
                "Bis zum nächsten Mal!"
            ),
            UserIntent.IDENTITY_OR_CAPABILITIES: (
                "Ich bin der **DigiHochX Research Assistant**, entwickelt an der Universität Hildesheim "
                "in der Arbeitsgruppe Informationssysteme und Unternehmensmodellierung (ISUM) unter der "
                "Leitung von Prof. Dr. Ralf Knackstedt (IT-Studienprojekt Master – Chatbot-Werkstatt, Use Case 3).\n\n"
                "Ich unterstütze dich bei der Analyse wissenschaftlicher Literatur, der Unterscheidung deskriptiver "
                "und präskriptiver Forschungsbeiträge sowie bei der Entwicklung einer integrierten Forschungsagenda für DigiHochX.\n\n"
                "**Meine Kernfähigkeiten:**\n"
                "- 📚 **Literaturanalyse & Grounding:** Quellenbasierte Analyse mit exakter Seitenzitation\n"
                "- 🔬 **Deskriptiv vs. Präskriptiv:** Trennung von empirischem Status quo und Gestaltungslösungen\n"
                "- 🔗 **Interdisziplinäre Integration:** Verbindung von Organisationspädagogik und Wirtschaftsinformatik\n"
                "- ⚡ **Konflikt- & Schnittstellenanalyse:** Untersuchung von Spannungen zwischen Verwaltung, Forschung und Lehre\n"
                "- 🔍 **Forschungslücken & Forschungsfragen:** Systematische Ableitung fundierter Fragestellungen für eine Forschungsagenda"
            ),
            UserIntent.LANGUAGE_REQUEST: (
                "Selbstverständlich! Ich passe mich gerne an. "
                "Wie kann ich dich bei deiner wissenschaftlichen Recherche zu DigiHochX unterstützen?"
            ),
            UserIntent.AMBIGUOUS_CLARIFICATION: (
                "Willkommen beim DigiHochX Research Assistant! Wie kann ich dich heute bei deiner Forschungsarbeit unterstützen?\n\n"
                "Du kannst mir konkrete wissenschaftliche Fragen zu den indexierten Dokumenten stellen "
                "(z. B. zu Business-IT-Alignment, Organisationskultur, organisationalem Lernen oder Schnittstellenkonflikten), "
                "oder methodische Auswertungen im Research Workspace anfordern."
            ),
        },
        "en": {
            UserIntent.GREETING: (
                "Hello! Welcome to the DigiHochX Research Assistant. "
                "How can I assist you with your scientific research today?"
            ),
            UserIntent.ACKNOWLEDGEMENT: (
                "You're very welcome! If you have further questions or need deeper "
                "scientific analysis on the documents, feel free to ask anytime."
            ),
            UserIntent.FAREWELL: (
                "Goodbye! Wishing you great success with your research on DigiHochX. "
                "Until next time!"
            ),
            UserIntent.IDENTITY_OR_CAPABILITIES: (
                "I am the **DigiHochX Research Assistant**, developed at the University of Hildesheim "
                "in the Research Group Information Systems and Enterprise Modelling (ISUM) led by "
                "Prof. Dr. Ralf Knackstedt (IT Study Project Master – Chatbot-Werkstatt, Use Case 3).\n\n"
                "I support you in analyzing scientific literature, distinguishing descriptive and "
                "prescriptive research contributions, and developing an integrated Research Agenda for DigiHochX.\n\n"
                "**My core capabilities:**\n"
                "- 📚 **Literature Analysis & Grounding:** Evidence-based analysis with exact page citations\n"
                "- 🔬 **Descriptive vs. Prescriptive:** Differentiating empirical status quo from design artifacts\n"
                "- 🔗 **Interdisciplinary Integration:** Bridging Organizational Pedagogy and Business Information Systems\n"
                "- ⚡ **Tension & Interface Analysis:** Exploring conflicts between administration, research, and teaching\n"
                "- 🔍 **Research Gaps & Questions:** Methodical derivation of research questions for a research agenda"
            ),
            UserIntent.LANGUAGE_REQUEST: (
                "Yes, absolutely! I will answer your questions in English from now on. "
                "How can I assist your scientific research on DigiHochX today?"
            ),
            UserIntent.AMBIGUOUS_CLARIFICATION: (
                "Welcome to the DigiHochX Research Assistant! How can I support your scientific research today?\n\n"
                "You can ask specific questions about the indexed literature "
                "(e.g., Business-IT alignment, organizational culture, organizational learning, or interface tensions), "
                "or request methodological analyses in the Research Workspace."
            ),
        }
    }

    @classmethod
    def handle_simplification(
        cls,
        chat_history: Optional[List[Dict[str, str]]],
        language: str = "de",
        gwdg_client: Optional[GWDGClient] = None,
        model: Optional[str] = None
    ) -> str:
        """Erklärt den zuletzt diskutierten wissenschaftlichen Begriff einfacher."""
        # Nach der letzten Assistenten-Antwort in der Historie suchen
        last_assistant_msg = None
        if chat_history:
            for msg in reversed(chat_history):
                if msg.get("role") == "assistant" and msg.get("content"):
                    last_assistant_msg = msg.get("content")
                    break

        if not last_assistant_msg:
            if language == "en":
                return (
                    "I'd be glad to simplify a concept! Which specific term or concept from DigiHochX "
                    "(e.g., *Business-IT Alignment*, *Organisational Learning Capacity*, *Competing Values Framework*, "
                    "or *DLOQ*) would you like me to explain more simply?"
                )
            return (
                "Gerne! Welchen wissenschaftlichen Begriff oder welches Konzept aus DigiHochX "
                "(z. B. *Business-IT-Alignment*, *Organisational Learning Capacity*, *Competing Values Framework* "
                "oder *DLOQ*) möchtest du einfacher erklärt haben?"
            )

        # Wenn eine vorherige Antwort vorliegt, bereiten wir eine vereinfachte Zusammenfassung vor
        if gwdg_client and gwdg_client.is_configured:
            prompt_instruction = (
                "Erkläre die Kernaussage und die zentralen wissenschaftlichen Begriffe der folgenden "
                "Antwort in einfachen, verständlichen Worten, ohne Fachjargon, aber unter Beibehaltung der inhaltlichen Korrektheit:"
                if language == "de"
                else "Explain the core message and key scientific terms from the following answer in simple, accessible language without academic jargon:"
            )
            messages = [
                {"role": "system", "content": "Du bist ein verständlicher wissenschaftlicher Erklärer."},
                {"role": "user", "content": f"{prompt_instruction}\n\nANTWORT:\n{last_assistant_msg[:1200]}"}
            ]
            try:
                simplified = gwdg_client.generate(messages=messages, model=model, max_tokens=600)
                if simplified and len(simplified.strip()) > 30:
                    return simplified
            except Exception as e:
                logger.warning("Vereinfachung via GWDG fehlgeschlagen: %s", e)

        # Deterministische Vorlage mit Bezugnahme
        if language == "en":
            return (
                "### Simplified Explanation\n\n"
                "In simple terms, our research examines how digital systems (such as administrative IT platforms) "
                "interact with human organizational culture at universities. Often, technology demands formal rules "
                "and standardization, while academic researchers and educators value autonomy, trust, and flexibility. "
                "DigiHochX investigates these friction points and explores how collaborative learning can bridge this gap."
            )
        return (
            "### Einfach erklärt\n\n"
            "In einfachen Worten ausgedrückt: Unsere Forschung untersucht, wie digitale IT-Systeme und die "
            "Kultur von Hochschulen zusammenwirken. Oft fordert die Technik feste Regeln und Standardisierung, "
            "während Lehrende und Forschende Freiräume, Vertrauen und Flexibilität brauchen. "
            "DigiHochX erforscht genau diese Reibungen an den Schnittstellen und sucht nach Wegen, "
            "wie Verwaltung, Forschung und Lehre durch gemeinsames Lernen besser zusammenarbeiten können."
        )

    @classmethod
    def respond(
        cls,
        intent_result: IntentResult,
        user_query: str,
        language: str = "de",
        chat_history: Optional[List[Dict[str, str]]] = None,
        gwdg_client: Optional[GWDGClient] = None,
        model: Optional[str] = None
    ) -> str:
        """Erzeugt eine sofortige, qualitativ hochwertige Konversationsantwort."""
        lang = intent_result.requested_language or language
        if lang not in ("de", "en"):
            lang = "de"

        # Fall 1: Sprachwechsel-Anfrage
        if intent_result.intent == UserIntent.LANGUAGE_REQUEST:
            if intent_result.requested_language == "en" or "english" in user_query.lower():
                return (
                    "Yes, absolutely! I will converse and answer your research questions in English from now on. "
                    "How can I assist your scientific work on DigiHochX today?"
                )
            return (
                "Selbstverständlich! Ich antworte dir ab sofort auf Deutsch. "
                "Wie kann ich dich heute bei deiner Forschungsarbeit zu DigiHochX unterstützen?"
            )

        # Fall 2: Spezifische Begrüßung mit Tageszeit
        if intent_result.intent == UserIntent.GREETING:
            q_lower = user_query.lower()
            if "morgen" in q_lower or "morning" in q_lower:
                if lang == "en":
                    return "Good morning! Welcome to the DigiHochX Research Assistant. How can I support your scientific research today?"
                return "Guten Morgen! Willkommen beim DigiHochX Research Assistant. Wie kann ich dich heute bei deiner wissenschaftlichen Arbeit unterstützen?"
            elif "abend" in q_lower or "evening" in q_lower:
                if lang == "en":
                    return "Good evening! Welcome to the DigiHochX Research Assistant. How can I assist your research today?"
                return "Guten Abend! Willkommen beim DigiHochX Research Assistant. Wie kann ich dich heute bei deiner wissenschaftlichen Arbeit unterstützen?"
            return cls.RESPONSES[lang][UserIntent.GREETING]

        # Fall 3: Begriff einfacher erklären
        if intent_result.intent == UserIntent.SIMPLIFICATION_REQUEST:
            return cls.handle_simplification(
                chat_history=chat_history,
                language=lang,
                gwdg_client=gwdg_client,
                model=model
            )

        # Fall 4: Standard-Dialogantworten
        resp_dict = cls.RESPONSES.get(lang, cls.RESPONSES["de"])
        return resp_dict.get(
            intent_result.intent,
            resp_dict[UserIntent.GREETING]
        )

