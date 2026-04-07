import os
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

_CLIENT_ID = os.getenv("EXPA_CLIENT_ID")
_CLIENT_SECRET = os.getenv("EXPA_CLIENT_SECRET")
# Must match the redirect URI registered for this OAuth app (path + port + scheme, exact string).
_REDIRECT_URI = os.getenv("EXPA_REDIRECT_URI")
_GQL_ENDPOINT = os.getenv("AIESEC_GRAPHQL_ENDPOINT")
_TOKEN_URL = "https://auth.aiesec.org/oauth/token"

_CURRENT_PERSON_QUERY = """
query {
    currentPerson {
        id
        email
        full_name
        first_name
        last_name
    }
}
"""


class CodePayload(BaseModel):
    code: str


def _authorize_url() -> str:
    if not _CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="EXPA_CLIENT_ID is not set. Add EXPA_* variables to server/.env.",
        )
    params = {
        "response_type": "code",
        "client_id": _CLIENT_ID,
        "redirect_uri": _REDIRECT_URI,
    }
    scope = os.getenv("EXPA_OAUTH_SCOPE", "").strip()
    if scope:
        params["scope"] = scope
    return f"https://auth.aiesec.org/oauth/authorize?{urlencode(params)}"


@router.get("/login")
def login():
    """Redirect the browser to the EXPA OAuth consent screen."""
    return RedirectResponse(url=_authorize_url())


@router.post("/exchange")
async def exchange(payload: CodePayload):
    """Exchange an authorization code for a user_id via EXPA GraphQL."""
    if not _CLIENT_ID or not _CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="EXPA_CLIENT_ID or EXPA_CLIENT_SECRET missing in server/.env",
        )
    async with httpx.AsyncClient() as client:
        token_res = await client.post(_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": payload.code,
            "redirect_uri": _REDIRECT_URI,
            "client_id": _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
        })

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Token exchange failed")

    access_token = token_res.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    async with httpx.AsyncClient() as client:
        gql_res = await client.post(
            _GQL_ENDPOINT,
            json={"query": _CURRENT_PERSON_QUERY},
            headers={
                # AIESEC GraphQL expects the raw EXPA token in Authorization.
                "Authorization": access_token,
                "Content-Type": "application/json",
            },
        )

    if gql_res.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"GraphQL request failed ({gql_res.status_code}): {gql_res.text[:300]}",
        )

    person = gql_res.json().get("data", {}).get("currentPerson")
    if not person:
        raise HTTPException(status_code=502, detail="Could not retrieve user info")

    name = person.get("full_name") or (
        f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    )
    return {"user_id": str(person["id"]), "name": name, "email": person.get("email")}
