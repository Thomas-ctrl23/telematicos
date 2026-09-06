"""
FastAPI Serverless Application for Dataset Cleaning with Pandas.
Compatible with local development and Vercel Serverless Functions.
"""

import io
import json
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd

from api.cleaner import DataCleaner

logger = logging.getLogger("uvicorn")
app = FastAPI(
    title="DataClean AI - Pandas Dataset Cleaner",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Enable CORS for local dev and cross-origin frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_uploaded_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Safely parses an uploaded CSV or Excel file into a pandas DataFrame."""
    lower_name = (filename or "").lower()

    if lower_name.endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo leer el archivo Excel: {str(e)}"
            )

    # For CSV / TSV, try different encodings and delimiters
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    for enc in encodings:
        try:
            # Auto-detect delimiter using csv sniffer or try comma / semicolon
            sample = file_bytes[:4096].decode(enc, errors="ignore")
            sep = ";" if sample.count(";") > sample.count(",") else ","
            if "\t" in sample and sample.count("\t") > sample.count(sep):
                sep = "\t"

            df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding=enc)
            return df
        except UnicodeDecodeError:
            continue
        except Exception:
            continue

    # Fallback with python engine
    try:
        return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al analizar el archivo CSV: {str(e)}"
        )


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "DataClean Pandas API", "version": "1.0.0"}


@app.post("/api/analyze")
async def analyze_dataset(file: UploadFile = File(...)):
    """
    Receives an uploaded CSV or Excel file and returns an in-depth analysis
    including missing cells, duplicate rows, outliers, and typo candidates.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="El archivo subido está vacío.")

        df = parse_uploaded_file(contents, file.filename or "dataset.csv")

        if df.empty:
            raise HTTPException(status_code=400, detail="El dataset no contiene filas ni datos válidos.")

        inspection = DataCleaner.inspect(df)
        inspection["filename"] = file.filename
        inspection["file_size_kb"] = round(len(contents) / 1024, 1)

        return JSONResponse(content=inspection)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")


@app.post("/api/clean")
async def clean_dataset(
    file: UploadFile = File(...),
    config: Optional[str] = Form("{}"),
):
    """
    Applies the configured Pandas cleaning rules:
    - Missing cells removal
    - Duplicate rows removal
    - Statistical outliers treatment
    - Typographical corrections
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="El archivo subido está vacío.")

        df = parse_uploaded_file(contents, file.filename or "dataset.csv")
        clean_config = json.loads(config or "{}")

        cleaned_df, results = DataCleaner.clean(df, clean_config)
        results["filename"] = file.filename

        return JSONResponse(content=results)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la limpieza: {str(e)}")


@app.post("/api/export")
async def export_dataset(
    file: UploadFile = File(...),
    config: Optional[str] = Form("{}"),
    export_format: Optional[str] = Form("csv"),
):
    """
    Cleans the uploaded file with the specified config and streams the clean
    dataset back as a downloadable CSV or Excel file.
    """
    try:
        contents = await file.read()
        df = parse_uploaded_file(contents, file.filename or "dataset.csv")
        clean_config = json.loads(config or "{}")

        cleaned_df, _ = DataCleaner.clean(df, clean_config)
        base_name = (file.filename or "dataset").rsplit(".", 1)[0]

        if export_format == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                cleaned_df.to_excel(writer, index=False, sheet_name="Cleaned_Data")
            output.seek(0)
            filename = f"{base_name}_limpio.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            output = io.BytesIO()
            cleaned_df.to_csv(output, index=False, encoding="utf-8-sig")
            output.seek(0)
            filename = f"{base_name}_limpio.csv"
            media_type = "text/csv; charset=utf-8"

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    except Exception as e:
        logger.error(f"Error exporting dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error al exportar: {str(e)}")
