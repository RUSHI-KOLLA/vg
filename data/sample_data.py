from typing import List, Dict, Any

SAMPLE_CASES = {
    "politician_foreign_links": {
        "question": "Does Senator Johnson have links to the Russian government?",
        "entities": {
            "senator_johnson": {"name": "Senator Johnson", "type": "person", "role": "US Senator"},
            "russia": {"name": "Russia", "type": "country"},
            "kremlin": {"name": "Kremlin", "type": "organization"},
            "moscow_meeting": {"name": "Moscow Meeting 2023", "type": "event"},
        },
        "evidence": [
            {
                "id": "ev1",
                "claim_id": 1,
                "source_name": "Washington Post",
                "source_type": "news",
                "date": "2023-06-15",
                "headline": "Senator Johnson attended diplomatic summit in Moscow",
                "content": "Senator Johnson was observed at the Russian International Affairs Council summit in Moscow on June 15, 2023. Multiple diplomatic sources confirmed his presence.",
                "url": "https://example.com/article1",
                "entities_found": ["senator_johnson", "russia", "moscow_meeting"],
                "relevance": 0.9,
            },
            {
                "id": "ev2",
                "claim_id": 1,
                "source_name": "Kremlin Press",
                "source_type": "government",
                "date": "2023-06-15",
                "headline": "Official statement on international delegation",
                "content": "The Kremlin issued a statement welcoming international parliamentarians to Moscow, including delegates from the US Senate.",
                "url": "https://example.com/kremlin",
                "entities_found": ["kremlin", "russia"],
                "relevance": 0.7,
            },
            {
                "id": "ev3",
                "claim_id": 2,
                "source_name": "AP News",
                "source_type": "news",
                "date": "2023-08-20",
                "headline": "Campaign finance records show foreign donations",
                "content": "Campaign finance records show a consulting firm with ties to Russian business interests donated $50,000 to Johnson's re-election campaign.",
                "url": "https://example.com/article2",
                "entities_found": ["senator_johnson"],
                "relevance": 0.85,
            },
            {
                "id": "ev4",
                "claim_id": 2,
                "source_name": "FEC Records",
                "source_type": "public_record",
                "date": "2023-08-15",
                "headline": "FEC Campaign Finance Report Q3 2023",
                "content": "Official FEC records show donations from 'Baltic Consulting Group LLC' - registered in Delaware but linked to Russian nationals.",
                "url": "https://example.com/fec",
                "entities_found": ["senator_johnson"],
                "relevance": 0.95,
            },
            {
                "id": "ev5",
                "claim_id": 3,
                "source_name": "C-SPAN",
                "source_type": "speech",
                "date": "2023-09-10",
                "headline": "Senate Floor Speech on Russia Policy",
                "content": "Senator Johnson gave a speech advocating for reduced sanctions on Russian energy exports, citing 'pragmatic foreign policy'.",
                "url": "https://example.com/speech",
                "entities_found": ["senator_johnson", "russia"],
                "relevance": 0.8,
            },
            {
                "id": "ev6",
                "claim_id": 3,
                "source_name": "Senator Johnson's Website",
                "source_type": "speech",
                "date": "2023-09-10",
                "headline": "Transcript of floor speech",
                "content": "Full transcript shows Johnson argued for 'engagement over confrontation' with Russia.",
                "url": "https://example.com/johnson",
                "entities_found": ["senator_johnson", "russia"],
                "relevance": 0.75,
            },
            {
                "id": "ev7",
                "claim_id": 1,
                "source_name": "Johnson's Office Statement",
                "source_type": "press_release",
                "date": "2023-06-16",
                "headline": "Statement on Moscow visit",
                "content": "Senator Johnson's office stated the visit was part of a bipartisan congressional delegation to discuss 'bilateral relations'.",
                "url": "https://example.com/statement",
                "entities_found": ["senator_johnson", "russia"],
                "relevance": 0.6,
            },
            {
                "id": "ev8",
                "claim_id": 2,
                "source_name": "Bloomberg",
                "source_type": "news",
                "date": "2023-11-05",
                "headline": "Russian-linked donations under investigation",
                "content": "FBI has opened an investigation into foreign donations to multiple Senate campaigns, including Johnson's.",
                "url": "https://example.com/fbi",
                "entities_found": ["senator_johnson"],
                "relevance": 0.7,
            },
        ]
    },
    "political_event_coordination": {
        "question": "Were the 2024 protests in country X coordinated by foreign actors?",
        "entities": {},
        "evidence": []
    }
}

def get_case(case_name: str) -> Dict[str, Any]:
    return SAMPLE_CASES.get(case_name, {})

def get_all_cases() -> List[str]:
    return list(SAMPLE_CASES.keys())

def get_sample_evidence(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return relevant sample evidence based on claims"""
    question = claims[0].get("claim_text", "") if claims else ""
    question_lower = question.lower()
    
    if "russian" in question_lower or "foreign" in question_lower or "politician" in question_lower:
        return SAMPLE_CASES["politician_foreign_links"]["evidence"]
    
    return []
