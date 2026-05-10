from pydantic import BaseModel


class ReviewAction(BaseModel):
    review_id: int
    action: str
    message: str | None = None
