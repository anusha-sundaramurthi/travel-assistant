from openai import OpenAI
from src.retriever import retrieve_docs
from src.config import NVIDIA_API_KEY, NVIDIA_BASE_URL, CHAT_MODEL

# ── LLM client (NVIDIA NIM, OpenAI-compatible) ────────────
_client = OpenAI(
    api_key=NVIDIA_API_KEY,
    base_url=NVIDIA_BASE_URL
)

def _chat(messages: list[dict], temperature: float = 0.7) -> str:
    resp = _client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=1500,
    )
    return resp.choices[0].message.content.strip()


# ── Per-session memory store ───────────────────────────────
_memory_store: dict[str, list[dict]] = {}   # session_id → list of {role, content}

def get_history(session_id: str) -> list[dict]:
    return _memory_store.setdefault(session_id, [])

def save_turn(session_id: str, user: str, assistant: str) -> None:
    history = get_history(session_id)
    history.append({"role": "user",      "content": user})
    history.append({"role": "assistant", "content": assistant})

def clear_memory(session_id: str) -> None:
    _memory_store.pop(session_id, None)


# ── Language instruction ───────────────────────────────────
def _lang_instruction(language: str) -> str:
    return (
        f"\n\nLANGUAGE INSTRUCTION:\n"
        f"You MUST respond ENTIRELY in {language}.\n"
        f"Every word of your answer must be in {language}.\n"
        f"Do not mix any other language.\n"
        f"Even if the question is in a different language, answer in {language}."
    )


# ── Query rewriter ─────────────────────────────────────────
REWRITE_SYSTEM = (
    "You are a query rewriter for a travel assistant.\n"
    "Your ONLY job is to rewrite the user's latest question so it is completely "
    "self-contained and explicit — replacing all vague pronouns and references "
    "(like 'there', 'it', 'that place', 'both', 'the first one', 'that city') "
    "with the actual destination names found in the conversation history.\n"
    "Rules:\n"
    "- If the question mentions multiple destinations implicitly, name ALL of them.\n"
    "- If the question is already explicit and clear, return it unchanged.\n"
    "- Return ONLY the rewritten question. No explanation. No extra text.\n"
    "- Do not answer the question. Just rewrite it.\n"
    "- Always rewrite in English regardless of input language."
)

VAGUE_WORDS = [
    "there", "it", "that place", "both", "the city",
    "that country", "first one", "second one", "those",
    "the destination", "that", "here", "same place"
]

def rewrite_query(raw_query: str, history: list[dict]) -> str:
    if not history:
        return raw_query
    if not any(w in raw_query.lower() for w in VAGUE_WORDS):
        print(f"[QueryRewriter] Already explicit — skipping: '{raw_query}'")
        return raw_query

    history_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history
    )
    msgs = [
        {"role": "system",  "content": REWRITE_SYSTEM + f"\n\nConversation history:\n{history_text}"},
        {"role": "user",    "content": f"Rewrite this question to be explicit: {raw_query}"}
    ]
    rewritten = _chat(msgs, temperature=0)
    print(f"[QueryRewriter] '{raw_query}' → '{rewritten}'")
    return rewritten


# ── Prompts ────────────────────────────────────────────────
PDF_SYSTEM = """You are an expert and friendly AI Travel Assistant.
Use the following travel guide context to answer the user's question.

CRITICAL RULES:
1. Read the user's question and identify the destination they are asking about.
2. Read the context carefully.
3. Ask yourself: "Does this context match BOTH the destination AND the actual topic?"
4. If YES → answer ONLY using the provided context.
5. NEVER add places, hotels, attractions, activities, prices, or facts not in the context.

STRICT PDF MODE:
- Use ONLY information explicitly present in the context.
- NEVER invent attractions, hotels, restaurants, activities, or cities.
- If the PDF has only 2 places, mention only those 2 places.
- Do NOT expand beyond the provided context.

FILTERING RULE:
- Extract ONLY sentences directly related to the user's question.
- If user asks about beaches, ignore hotels, culture, food, temples.
- If user asks about hotels, ignore attractions and itineraries.
- Never summarize the whole chunk unless the user explicitly asks.

RETURN 'NO_PDF_CONTEXT' if and only if:
- Context has ZERO relevant info about the user's question.
- Return ONLY the single word: NO_PDF_CONTEXT — no emoji, no explanation.

FORMAT:
- For trip plans: use 📅 Day 1, 📅 Day 2 headers with bullet points.
- For hotels: List with Luxury / Mid-range / Budget categories.
- For food/activities/beaches: categorised lists.
- NEVER use "Morning:", "Afternoon:", "Evening:" labels.
- Write naturally like helping a friend.
{lang}

Context from travel guides:
{context}

Conversation so far:
{history}
"""

GENERAL_SYSTEM = """You are an expert AI Travel Assistant.

⚠️ The user's question is NOT covered by uploaded PDF guides.
You are answering from your GENERAL TRAVEL KNOWLEDGE.

INSTRUCTIONS:
1. Provide helpful, accurate travel information.
2. For trip plans: write natural flowing paragraphs, 3–5 activities per day.
3. For hotels: Luxury / Mid-range / Budget categories.
4. For food/activities: organised lists.
5. Be friendly and engaging.
6. NEVER use "Morning:", "Afternoon:", "Evening:" labels.
{lang}

Conversation so far:
{history}
"""


# ── Main answer function ───────────────────────────────────
def generate_answer(
    query:       str,
    session_id:  str  = "default",
    use_general: bool = False,
    language:    str  = "English"
) -> dict:
    history  = get_history(session_id)
    lang_ins = _lang_instruction(language)

    # ── Translate non-ASCII queries to English for search ──
    if not all(ord(c) < 128 for c in query):
        print(f"[Generator] Non-English query detected, translating...")
        translated = _chat([
            {"role": "system", "content": "You are a translator. Translate to English. Return only the translation."},
            {"role": "user",   "content": query}
        ], temperature=0)
        query_for_search = translated
        print(f"[Generator] English: '{query_for_search}'")
    else:
        query_for_search = query

    # ── Spell-correct the search query ────────────────────
    corrected = _chat([
        {"role": "system", "content": "Correct spelling mistakes in this travel query. Return ONLY the corrected query. Do not change meaning."},
        {"role": "user",   "content": query_for_search}
    ], temperature=0)
    query_for_search = corrected.strip()
    print(f"[Generator] Corrected query: '{query_for_search}'")

    # ── Rewrite vague query ────────────────────────────────
    rewritten_query = rewrite_query(query_for_search, history)
    history_text    = "\n".join(
        f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}"
        for m in history
    )

    # ── Path A: General knowledge ──────────────────────────
    if use_general:
        print(f"[Generator] General knowledge path for: '{query}'")
        system = GENERAL_SYSTEM.format(lang=lang_ins, history=history_text)
        answer = _chat([
            {"role": "system", "content": system},
            {"role": "user",   "content": query}
        ])
        save_turn(session_id, query, answer)
        return {"answer": answer, "rewritten_query": rewritten_query, "has_pdf_context": False}

    # ── Path B: PDF retrieval ──────────────────────────────
    docs    = retrieve_docs(rewritten_query)
    context = "\n".join(docs)

    if not context.strip():
        print(f"[Generator] No PDF context for: '{query}'")
        return {"answer": None, "rewritten_query": rewritten_query, "has_pdf_context": False}

    system = PDF_SYSTEM.format(lang=lang_ins, context=context, history=history_text)
    answer = _chat([
        {"role": "system", "content": system},
        {"role": "user",   "content": query}
    ])

    if "NO_PDF_CONTEXT" in answer:
        print("[Generator] LLM detected irrelevant context → asking user")
        return {"answer": None, "rewritten_query": rewritten_query, "has_pdf_context": False}

    save_turn(session_id, query, answer)
    return {"answer": answer, "rewritten_query": rewritten_query, "has_pdf_context": True}
