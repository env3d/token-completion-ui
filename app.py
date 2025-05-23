from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root (/)
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# Allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load pre-trained model and tokenizer
model_name = "Qwen/Qwen2.5-0.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

class InputText(BaseModel):
    text: str

@app.post("/predict")
async def get_token_probabilities(input_text: InputText):
    sentence = input_text.text
    inputs = tokenizer(sentence, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    last_token_logits = logits[0, -1, :]
    probabilities = torch.nn.functional.softmax(last_token_logits, dim=-1)

    top_k = 10
    top_k_values, top_k_indices = torch.topk(probabilities, top_k)

    # Not decoding automatically
    # top_k_tokens = tokenizer.convert_ids_to_tokens(top_k_indices.tolist())
    # print(top_k_tokens)
    # result = [{"token": token.replace('Ġ', '').replace('Ċ','\n'), "probability": prob.item()} for token, prob in zip(top_k_tokens, top_k_values)]
    
    top_k_tokens = [tokenizer.decode([token_id]) for token_id in top_k_indices.tolist()]
    print(top_k_tokens)
    result = [{"token": token, "probability": prob.item()} for token, prob in zip(top_k_tokens, top_k_values)]
    
    return result

