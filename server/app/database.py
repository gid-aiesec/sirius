from pinecone import Pinecone
from app.config import settings

def get_pinecone_index():
    """
    Initializes the connection to Pinecone and returns the Index object.
    """
    api_key = settings.PINECONE_API_KEY
    index_name = settings.PINECONE_INDEX_NAME

    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in the .env file!")

    try:
        # Initialize the Pinecone client
        pc = Pinecone(api_key=api_key)
        
        # Connect to the specific index
        index = pc.Index(index_name)
        print(f"Successfully connected to Pinecone Index: {index_name}")
        
        return index
    
    except Exception as e:
        print(f"Failed to connect to Pinecone: {e}")
        raise e

# Create an index instance that can be imported by the FastAPI system later
vector_index = get_pinecone_index()