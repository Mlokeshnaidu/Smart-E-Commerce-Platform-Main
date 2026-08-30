import httpx

from core.config import settings


async def get_auth0_user_info(access_token: str) -> dict:
    url = f"https://{settings.AUTH0_DOMAIN}/userinfo"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        response.raise_for_status()
        return response.json()
