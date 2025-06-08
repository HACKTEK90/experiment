from flask import Flask, request, render_template, send_file
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import re
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    error = None
    url = None

    if request.method == "POST":
        url = request.form.get("url")
        try:
            # Fetch webpage content
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse HTML and extract text
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            text_elements = soup.find_all(["p", "h1", "h2", "h3"])
            raw_text = " ".join(element.get_text(strip=True) for element in text_elements)
            cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()

            # Limit text length for summarization
            max_input_length = 1024
            cleaned_text = cleaned_text[:max_input_length]

            # Summarize text
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            summary = summarizer(cleaned_text, max_length=150, min_length=50, do_sample=False)[0]["summary_text"]

            # Save summary to a temporary file
            with open("summary.txt", "w", encoding="utf-8") as file:
                file.write(summary)

        except Exception as e:
            error = f"Error processing the webpage: {str(e)}"
            summary = None

    return render_template("index.html", summary=summary, error=error, url=url)

@app.route("/download")
def download_summary():
    try:
        return send_file("summary.txt", as_attachment=True, download_name="summary.txt")
    except FileNotFoundError:
        return "Summary file not found. Please generate a summary first.", 404

if __name__ == "__main__":
    app.run(debug=True)
