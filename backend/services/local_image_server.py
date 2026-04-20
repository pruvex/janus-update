from fastapi import FastAPI, Request
import uvicorn
import os
import torch
from diffusers import StableDiffusionPipeline

app = FastAPI()

# Modell beim Starten laden
model_id = "runwayml/stable-diffusion-v1-5"
print("Lade Modell in den Speicher... (kann dauern)")
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32).to("cpu")

@app.post("/sdapi/v1/txt2img")
async def txt2img(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "a dog")
    print(f"Generiere Bild für: {prompt}")
    
    image = pipe(prompt).images[0]
    
    # Speichern im Output-Verzeichnis
    output_dir = "C:/KI/Janus-Image-Engine-CPU/output"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, "gen.png")
    image.save(save_path)
    
    # Rückgabe im Format, das media_tools.py erwartet
    return {"images": [{"url": save_path}]}

@app.get("/")
def read_root():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8188)
