from sentence_transformers import SentenceTransformer
import os

# Define the local path to save the model
local_model_path = os.path.join(
    os.path.dirname(__file__), "model_cache", "all-MiniLM-L6-v2"
)

# Create the directory if it doesn't exist
os.makedirs(local_model_path, exist_ok=True)

# Download and save the model
print(f"Downloading model to {local_model_path}...")
model = SentenceTransformer("all-MiniLM-L6-v2")
model.save(local_model_path)
print("Model downloaded and saved successfully.")
