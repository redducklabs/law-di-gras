"""API shapes shared by every stream. Mirrored in frontend/src/api/types.ts.

Change only via a small `contract:` commit that updates both files.
"""

from typing import Literal

from pydantic import BaseModel, Field

SourceKind = Literal[
    "note", "communication", "task", "calendar_entry", "expense",
    "document", "custom_field", "contact", "matter",
]


class Rect(BaseModel):
    page: int  # 1-based
    x0: float  # 0..1, top-left origin
    y0: float
    x1: float
    y1: float


class Citation(BaseModel):
    source_id: str
    source_kind: SourceKind
    source_title: str
    date: str | None = None
    page: int | None = None
    quote: str
    char_start: int | None = None
    char_end: int | None = None
    rects: list[Rect] = Field(default_factory=list)
    verified: bool = False


class Fact(BaseModel):
    id: str
    label: str
    value: str
    amount: float | None = None
    date: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    verified: bool = False


class TimelineEvent(BaseModel):
    date: str
    label: str
    kind: Literal["incident", "treatment", "legal", "communication", "deadline"]
    is_future: bool = False
    major: bool = False  # one of the ~12 milestones worth showing on a compact strip
    citations: list[Citation] = Field(default_factory=list)


class ActionItem(BaseModel):
    title: str
    due_date: str | None = None
    owner: str | None = None
    status: Literal["overdue", "upcoming", "waiting"]
    waiting_on: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class TreatmentLine(BaseModel):
    provider: str
    contact_id: str | None = None
    first_visit: str | None = None
    last_visit: str | None = None
    visit_count: int | None = None
    billed: Fact | None = None
    citations: list[Citation] = Field(default_factory=list)


class MatterSummary(BaseModel):
    id: str
    display_number: str
    title: str
    client_name: str
    client_photo_url: str | None = None
    status: str
    opened_date: str | None = None


class Headline(BaseModel):
    status_line: str
    stage: str
    bullets: list[Fact] = Field(default_factory=list)


class Kpis(BaseModel):
    specials: Fact | None = None
    coverage: list[Fact] = Field(default_factory=list)
    case_value: Fact | None = None  # draft range, only when grounded
    firm_spent: Fact | None = None
    liens: list[Fact] = Field(default_factory=list)


class Dashboard(BaseModel):
    matter: MatterSummary
    generated_at: str
    cost_usd: float
    models: list[str] = Field(default_factory=list)
    headline: Headline
    timeline: list[TimelineEvent] = Field(default_factory=list)
    kpis: Kpis
    actions: list[ActionItem] = Field(default_factory=list)
    last_client_contact: Fact | None = None
    injuries: list[Fact] = Field(default_factory=list)
    treatment: list[TreatmentLine] = Field(default_factory=list)
    recent: list[Fact] = Field(default_factory=list)


class SourcePage(BaseModel):
    page_no: int
    width: float
    height: float
    ocr: bool


class SourceDetail(BaseModel):
    id: str
    kind: SourceKind
    title: str
    date: str | None = None
    author: str | None = None
    text: str
    page_count: int | None = None
    has_file: bool = False
    pages: list[SourcePage] = Field(default_factory=list)


class Passage(BaseModel):
    citation: Citation
    score: float
    snippet: str


class AskRequest(BaseModel):
    question: str


class Answer(BaseModel):
    answer_markdown: str  # [n] markers index into citations (1-based)
    citations: list[Citation] = Field(default_factory=list)


class Provider(BaseModel):
    contact_id: str
    name: str
    role: str | None = None


class ShareSections(BaseModel):
    status: bool = True
    coverage: bool = True
    treatment: bool = True
    requests: bool = True
    timeline: bool = False
    documents: bool = False


class ShareSettings(BaseModel):
    contact_id: str
    sections: ShareSections = Field(default_factory=ShareSections)
    source_ids: list[str] = Field(default_factory=list)
    token: str | None = None
    last_viewed_at: str | None = None


class SharedDocument(BaseModel):
    source_id: str
    title: str


class ProviderView(BaseModel):
    matter_title: str
    client_name: str
    provider_name: str
    stage: str
    status_line: str
    case_active: bool
    last_activity_date: str | None = None
    coverage: list[Fact] | None = None
    requests: list[ActionItem] | None = None
    treatment: list[TreatmentLine] | None = None
    liens: list[Fact] | None = None  # this provider's own lien(s), with treatment
    timeline: list[TimelineEvent] | None = None
    documents: list[SharedDocument] | None = None
