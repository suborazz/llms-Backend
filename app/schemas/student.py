from pydantic import BaseModel


class StudentSubmissionRequest(BaseModel):
    content_id: str
    response_type: str
    response_text: str | None = None
    response_url: str | None = None

