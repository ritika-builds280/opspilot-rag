import chromadb

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    name="opspilot_documents"
)

print("Total records:", collection.count())

records = collection.get(
    include=["documents", "metadatas"]
)

for index, metadata in enumerate(records["metadatas"]):
    print(f"\nRecord {index + 1}")
    print("Metadata:", metadata)