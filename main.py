from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import Agent, Runner, FileSearchTool
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

# ----------------------------------------------------------------------
# Agent setup
# ----------------------------------------------------------------------
file_search_tool = FileSearchTool(
    max_num_results=5,
    vector_store_ids=["vs_6868f43e68b48191905129c5a089c159"],
)


assistant_agent = Agent(
    name="Assistant",
    instructions=(
        "You're a helpful assistant. Use *only* the provided vector store to find the information. "
        "If you can’t find the answer, simply reply with 'I don't know'."
    ),
    tools=[file_search_tool],
)

# ----------------------------------------------------------------------
# FastAPI app setup
# ----------------------------------------------------------------------
app = FastAPI(
    title="BackAware Benefits Assistant API",
    description="Ask questions about BackAware benefits via a simple JSON interface.",
    version="1.0.0",
)
# CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse, tags=["frontend"])
def serve_homepage():
    """Serve the frontend HTML file."""
    index_path = Path("frontend/index.html")
    return index_path.read_text(encoding="utf-8")


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str


@app.post("/ask", response_model=QueryResponse, tags=["qa"])
async def ask_question(req: QueryRequest) -> QueryResponse:
    try:
        result = await Runner.run(assistant_agent, req.query)
        return QueryResponse(answer=result.final_output)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
