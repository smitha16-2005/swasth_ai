
import os
import chromadb

# Initialize ChromaDB — stores embeddings locally
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Use ChromaDB's default ONNX embedding function
# This avoids the heavy PyTorch/Sentence Transformers dependency.
collection = chroma_client.get_or_create_collection(
    name="icmr_guidelines"
)


def load_documents():
    """
    Loads all .txt files from docs/ folder into ChromaDB.
    Only runs if collection is empty.
    """
    if collection.count() > 0:
        print(f"ChromaDB already loaded with {collection.count()} chunks")
        return

    docs_path = "./docs"

    if not os.path.exists(docs_path):
        print("Docs folder not found. Skipping guideline loading.")
        return

    all_chunks = []
    all_ids = []
    all_metadata = []

    for filename in os.listdir(docs_path):
        if filename.endswith(".txt"):
            filepath = os.path.join(docs_path, filename)
            disease_name = filename.replace(".txt", "")

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = [
                content[i:i + 500]
                for i in range(0, len(content), 500)
            ]

            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"{disease_name}_chunk_{i}")
                all_metadata.append({
                    "disease": disease_name,
                    "source": filename
                })

    if all_chunks:
        collection.add(
            documents=all_chunks,
            ids=all_ids,
            metadatas=all_metadata
        )
        print(f"Loaded {len(all_chunks)} chunks into ChromaDB")
    else:
        print("No guideline documents found.")


def query_guidelines(symptoms: list, suspected_disease: str = None) -> str:
    """
    Searches ICMR guidelines for relevant clinical information.
    Returns the most relevant text chunks as context for the AI.
    """
    query = (
        f"{suspected_disease or ''} "
        f"{' '.join(symptoms)} symptoms treatment guidelines India"
    )

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    if not results["documents"][0]:
        return "No relevant guidelines found."

    context = "\n\n".join(results["documents"][0])
    return context


# Load documents when this module is imported
load_documents()
