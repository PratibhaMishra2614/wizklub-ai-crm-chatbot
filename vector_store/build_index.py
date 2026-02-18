import os
import faiss
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# Load local embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def split_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def build_vector_store():
    file_path = os.path.join("data", "raw", "wizklub_content.txt")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = split_text(text)

    embeddings = model.encode(chunks)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    os.makedirs("vector_store/faiss_index", exist_ok=True)

    faiss.write_index(index, "vector_store/faiss_index/index.faiss")
    np.save("vector_store/faiss_index/chunks.npy", np.array(chunks))

    print("✅ Vector database built successfully (local embeddings).")

if __name__ == "__main__":
    build_vector_store()
