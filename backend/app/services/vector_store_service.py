"""
Single interface for vector upsert/query/delete operations. Feature code
(rag_service, embedding_service) calls this, never Chroma or Pinecone
directly — switching providers is a one-line config change.
"""

import uuid
from abc import ABC, abstractmethod

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class VectorStoreProvider(ABC):
    @abstractmethod
    async def upsert(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict], namespace: str) -> None: ...

    @abstractmethod
    async def query(self, vector: list[float], top_k: int, namespace: str, filters: dict | None = None) -> list[dict]: ...

    @abstractmethod
    async def delete(self, ids: list[str], namespace: str) -> None: ...


class ChromaProvider(VectorStoreProvider):
    def __init__(self):
        import chromadb

        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

    def _collection(self, namespace: str):
        return self.client.get_or_create_collection(name=namespace or "default")

    async def upsert(self, ids, vectors, metadatas, namespace):
        try:
            self._collection(namespace).upsert(ids=ids, embeddings=vectors, metadatas=metadatas)
        except Exception as exc:
            logger.error("Chroma upsert failed: %s", exc)
            raise ExternalServiceException("Failed to index document chunks.") from exc

    async def query(self, vector, top_k, namespace, filters=None):
        try:
            results = self._collection(namespace).query(
                query_embeddings=[vector], n_results=top_k, where=filters or None
            )
        except Exception as exc:
            logger.error("Chroma query failed: %s", exc)
            raise ExternalServiceException("Vector search failed.") from exc

        matches = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        for chunk_id, distance, metadata in zip(ids, distances, metadatas):
            matches.append({"id": chunk_id, "score": 1 - distance, "metadata": metadata})
        return matches

    async def delete(self, ids, namespace):
        try:
            self._collection(namespace).delete(ids=ids)
        except Exception as exc:
            logger.warning("Chroma delete failed: %s", exc)


class PineconeProvider(VectorStoreProvider):
    def __init__(self):
        from pinecone import Pinecone

        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)

    async def upsert(self, ids, vectors, metadatas, namespace):
        try:
            records = [{"id": i, "values": v, "metadata": m} for i, v, m in zip(ids, vectors, metadatas)]
            self.index.upsert(vectors=records, namespace=namespace)
        except Exception as exc:
            logger.error("Pinecone upsert failed: %s", exc)
            raise ExternalServiceException("Failed to index document chunks.") from exc

    async def query(self, vector, top_k, namespace, filters=None):
        try:
            results = self.index.query(
                vector=vector, top_k=top_k, namespace=namespace, filter=filters or None, include_metadata=True
            )
        except Exception as exc:
            logger.error("Pinecone query failed: %s", exc)
            raise ExternalServiceException("Vector search failed.") from exc

        return [{"id": m.id, "score": m.score, "metadata": m.metadata} for m in results.matches]

    async def delete(self, ids, namespace):
        try:
            self.index.delete(ids=ids, namespace=namespace)
        except Exception as exc:
            logger.warning("Pinecone delete failed: %s", exc)


def get_vector_store() -> VectorStoreProvider:
    if settings.VECTOR_STORE_PROVIDER == "pinecone":
        return PineconeProvider()
    return ChromaProvider()


vector_store = get_vector_store()


def project_namespace(project_id: uuid.UUID) -> str:
    """Namespaces vectors per-project so retrieval never crosses workspace boundaries."""
    return f"project_{project_id}"
