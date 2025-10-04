from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn

app = FastAPI()

# app.mount("/static", StaticFiles(directory="pdf"), name="static")

@app.get("/{album_id}")
def provide_album(album_id: int):
    pdf_path = Path("pdf") / f"{album_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path=pdf_path, filename=f"{album_id}.pdf", media_type='application/pdf')
if __name__ =="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8080)