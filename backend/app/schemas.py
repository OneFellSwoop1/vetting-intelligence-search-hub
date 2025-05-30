from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

class SearchResult(BaseModel):
    source: Literal[
        "checkbook", "dbnyc", "nys_ethics", "senate_lda", "house_lda", "nyc_lobbyist"
    ]
    jurisdiction: Literal["NYC", "NYS", "Federal"]
    entity_name: str
    role_or_title: Optional[str]
    description: Optional[str]
    amount_or_value: Optional[str]
    filing_date: Optional[str]
    url_to_original_record: Optional[str]
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    total_hits: dict
    results: list[SearchResult] 