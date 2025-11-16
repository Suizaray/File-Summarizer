import os
import time
import pdfplumber
from openai import OpenAI

ABS_PATH_DIR = os.path.dirname(os.path.abspath(__file__))

WATCH_DIR = os.path.join(ABS_PATH_DIR, "watch")
OUT_DIR = os.path.join(ABS_PATH_DIR, "summaries")

client = OpenAI()

def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
    

def chunk_text(text, max_chars=3000):
    paragraphs = text.split("\n")
    chunks = []
    current = ""

    for p in paragraphs:
        if len(current) + len(p) + 1 > max_chars:
            chunks.append(current.strip())
            current = p + "\n"
        else:
            current += p + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


def read_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
            text += "\n"
    return text

def read_file(path):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return read_pdf(path)
    else:
        return read_text(path)
    
def hierarchical_summary(full_text):
    # 1. Chunk the document
    chunks = chunk_text(full_text)
    print(f"Document split into {len(chunks)} chunks.")

    # 2. Summarize each chunk individually
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i+1}/{len(chunks)}...")
        summary = summarize_text_block(chunk, purpose="Summarize this part of the document:")
        chunk_summaries.append(summary)

    # 3. Combine chunk summaries into a final summary
    combined_text = "\n".join(chunk_summaries)
    print("Generating final summary...")

    final_summary = summarize_text_block(
        combined_text,
        purpose="Combine these partial summaries into one overall, well-structured summary:"
    )

    return final_summary


    

def summarize_text_block(text, purpose="Summarize the following text:"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a concise summarization assistant."},
            {"role": "user", "content": f"{purpose}\n\n{text}"}
        ]
    )
    return response.choices[0].message.content.strip()


def summarize_text(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents in clear bullet points."},
            {"role": "user", "content": f"Summarize the following file:\n\n{text}"}
        ]
    )
    
    return response.choices[0].message.content.strip()

def process_file(file_path):
    print(f"Processing: {file_path}")
    
    text = read_file(file_path)

    # Use hierarchical summarization for ALL files
    summary = hierarchical_summary(text)

    name = os.path.basename(file_path)
    out_path = os.path.join(OUT_DIR, f"{name}_summary.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Saved summary to {out_path}")


def load_already_processed():
    processed = set()
    for filename in os.listdir(OUT_DIR):
        # summary format is: original_filename + "_summary.md"
        if filename.endswith("_summary.md"):
            original = filename.replace("_summary.md", "")
            processed.add(original)
    return processed

def run_agent():
    print("File Summarizer Agent running.")
    
    # Load already processed across runs
    processed = load_already_processed()

    while True:
        for filename in os.listdir(WATCH_DIR):
            path = os.path.join(WATCH_DIR, filename)

            if filename not in processed and os.path.isfile(path):
                process_file(path)
                processed.add(filename)
        
        time.sleep(2)  # check every 2 seconds


if __name__ == "__main__":
    run_agent()
