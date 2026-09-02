from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.loader import Chunk

EXTRA_KEYWORDS = {
    "transfer": ["transfer fee"],
    "yield": ["rental yield"],
    "rental": ["rental yield"],
    "anchor": ["anchor tenant"],
    "margalla": ["location premiums", "base price"],
    "premium": ["location premiums"],
    "cancel": ["cancel"],
    "refund": ["cancel"],
    "payment": ["payment plan"],
    "instal": ["payment plan"],
    "amenit": ["amenities"],
    "pool": ["amenities"],
    "possession": ["possession"],
    "discount": ["discount"],
    "overseas": ["discount"],
}


class SearchIndex:
    """TF-IDF search over document chunks."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        texts = [f"{c.document} {c.section}\n{c.text}" for c in chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, question: str, top_k: int = 4) -> list[tuple[Chunk, float]]:
        """Return only the top relevant chunks for a question."""
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix)[0].copy()

        q = question.lower()
        for word, phrases in EXTRA_KEYWORDS.items():
            if word not in q:
                continue
            for phrase in phrases:
                for i, chunk in enumerate(self.chunks):
                    haystack = f"{chunk.section}\n{chunk.text}".lower()
                    if phrase in haystack:
                        scores[i] += 0.15

        ranked = sorted(
            ((i, float(scores[i])) for i in range(len(self.chunks))),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for i, score in ranked:
            if score <= 0:
                break
            results.append((self.chunks[i], score))
            if len(results) >= top_k:
                break
        return results
