from fastapi import FastAPI, HTTPException, Response, File, UploadFile
import pandas as pd
import sqlite3
import json
import fitz
import re
from pdfquery import PDFQuery

app = FastAPI()

def push_data_to_sqlite():
    lookup_df = pd.read_csv('lookup.csv')
    products_df = pd.read_csv('mapToProducts.csv')
    conn = sqlite3.connect('data.db')
    lookup_df.to_sql('lookup', conn, if_exists='replace', index=False)
    products_df.to_sql('products', conn, if_exists='replace', index=False)
    conn.close()

push_data_to_sqlite()

def load_lookup_mapping():
    conn = sqlite3.connect('data.db')
    lookup_mapping = pd.read_sql_query("SELECT assigned_integer, belegnummer FROM lookup", conn)
    conn.close()
    return dict(zip(lookup_mapping['belegnummer'], lookup_mapping['assigned_integer']))

@app.get("/entries/{document_number}", response_class=Response)
async def get_entries(document_number: str):
    conn = sqlite3.connect('data.db')
    query = """
    SELECT l.assigned_integer, p.belegnummer, p.posnummer as entry_number, p.artikelnummer as product_numbers
    FROM products p
    JOIN lookup l ON p.belegnummer = l.belegnummer
    WHERE p.belegnummer = ?
    """
    related_entries = pd.read_sql_query(query, conn, params=[document_number])
    conn.close()
    if related_entries.empty:
        raise HTTPException(status_code=404, detail=f"No entries found for document number {document_number}")
    output_csv = related_entries.to_csv(index=False)
    return Response(content=output_csv, media_type="text/csv")


@app.get("/database/")
async def get_database():
    conn = sqlite3.connect('data.db')
    lookup_data = pd.read_sql_query("SELECT * FROM lookup", conn)
    products_data = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    lookup_data = lookup_data.where(pd.notnull(lookup_data), None)
    products_data = products_data.where(pd.notnull(products_data), None)
    database_data = {
        'lookup': lookup_data.to_dict(orient='records'),
        'products': products_data.to_dict(orient='records')
    }
    return json.dumps(database_data)




import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile
import pandas as pd
import re

app = FastAPI()

@app.post("/process-pdf/")
async def process_pdf(pdf_file: UploadFile = File(...)):
    try:
        # Save PDF from request
        temp_file_path = "temp_pdf.pdf"
        with open(temp_file_path, "wb") as f:
            f.write(await pdf_file.read())

        # Use PDFQuery to extract text
        pdf = PDFQuery(temp_file_path)
        pdf.load()

        extracted_text = pdf.tree.xpath('//LTTextLineHorizontal/text()')
        
        # Close the PDFQuery object after extraction
        pdf.tree = None

    # You can further process the extracted text as needed
    
        return extracted_text
    except Exception as e:
        print(e)
