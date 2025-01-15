from pydantic import BaseModel, HttpUrl, Field

class FetchPRPayload(BaseModel):
    github_repo_url: HttpUrl = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., description="Pull Request number")
    access_token: str = Field(None, description="Optional GitHub access token")
