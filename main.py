from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
from datetime import datetime

app = FastAPI(title="Google Index Checker API")

# Allow all origins so your HTML file can call this API from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your Serper.dev API key — real Google Search results
SERPER_API_KEY = "8e3b286904df390d26a4a1fcb7f82ed199fe94c0"

class CheckRequest(BaseModel):
    urls: List[str]

@app.get("/")
def root():
    return {"status": "Google Index Checker API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/check-index")
async def check_index(request: CheckRequest):
    urls = request.urls[:10]  # max 10 URLs
    results = []
    indexed_count = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for url in urls:
            # Ensure URL has scheme
            if not url.startswith("http"):
                url = "https://" + url

            try:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": SERPER_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": f"site:{url}",
                        "num": 1,
                        "gl": "us",
                        "hl": "en"
                    }
                )

                data = resp.json()

                # Check if page is indexed
                total = int(data.get("searchInformation", {}).get("totalResults", 0))
                has_organic = len(data.get("organic", [])) > 0
                has_answer = "answerBox" in data
                has_knowledge = "knowledgeGraph" in data
                is_indexed = total > 0 or has_organic or has_answer or has_knowledge

            except Exception:
                is_indexed = False

            if is_indexed:
                indexed_count += 1

            results.append({
                "url": url,
                "is_indexed": is_indexed,
                "checked_at": datetime.utcnow().isoformat(),
                "verify_link": f"https://www.google.com/search?q=site:{url}"
            })

    return {
        "total": len(results),
        "indexed": indexed_count,
        "not_indexed": len(results) - indexed_count,
        "results": results
    }
