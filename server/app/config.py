import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Central class to hold injected env variables
    """

    # expa oauth
    EXPA_CLIENT_ID: str = os.getenv("EXPA_CLIENT_ID")
    EXPA_CLIENT_SECRET: str = os.getenv("EXPA_CLIENT_SECRET")
    EXPA_REDIRECT_URI: str = os.getenv("EXPA_REDIRECT_URI")
    EXPA_TOKEN_URL: str = os.getenv("EXPA_TOKEN_URL")
    AIESEC_GRAPHQL_ENDPOINT: str = os.getenv("AIESEC_GRAPHQL_ENDPOINT")
    EXPA_OAUTH_SCOPE: str = os.getenv("AIESEC_GRAPHQL_ENDPOINT", "")

    # pinecone client
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")

    # supabase client
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

    # gemini client
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL")

settings = Settings()