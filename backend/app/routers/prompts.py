from fastapi import APIRouter
from app.models import PromptConfig, PromptConfigUpdate
from app import storage

router = APIRouter()


@router.get("/", response_model=PromptConfig)
def get_prompts():
    return storage.get_prompt_config()


@router.put("/", response_model=PromptConfig)
def update_prompts(body: PromptConfigUpdate):
    return storage.update_prompt_config(
        system_prompt=body.system_prompt,
        default_user_prompt=body.default_user_prompt,
    )
