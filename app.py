import os
import PyPDF2
from flask import Flask, render_template, request, redirect, send_file, jsonify

app = Flask(__name__)

# Função para buscar nomes no PDF
def buscar_nome_pdf(pdf_path, nomes):
    nomes_encontrados = {}
    nomes_nao_encontrados = []

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for nome in nomes:
            found_pages = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and nome in text:
                    found_pages.append(page_num)
            if found_pages:
                nomes_encontrados[nome] = found_pages
            else:
                nomes_nao_encontrados.append(nome)

    return nomes_encontrados, nomes_nao_encontrados

# Função para salvar páginas em PDFs separados
def salvar_pdfs(pdf_path, nomes_encontrados, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for nome, pages in nomes_encontrados.items():
            writer = PyPDF2.PdfWriter()
            for page in pages:
                writer.add_page(reader.pages[page])

            output_file = os.path.join(output_dir, f"{nome}.pdf")
            with open(output_file, "wb") as output_pdf:
                writer.write(output_pdf)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/processar", methods=["POST"])
def processar():
    try:
        pdf_file = request.files["pdf_file"]
        names_file = request.files["names_file"]
        output_dir = request.form["output_dir"]

        if not pdf_file or not names_file or not output_dir:
            return jsonify({"status": "error", "message": "Todos os arquivos devem ser selecionados."})

        pdf_path = os.path.join("temp", pdf_file.filename)
        os.makedirs("temp", exist_ok=True)
        pdf_file.save(pdf_path)

        names_path = os.path.join("temp", names_file.filename)
        names_file.save(names_path)

        with open(names_path, "r", encoding="utf-8") as f:
            nomes = [line.strip() for line in f.readlines()]

        nomes_encontrados, nomes_nao_encontrados = buscar_nome_pdf(pdf_path, nomes)
        salvar_pdfs(pdf_path, nomes_encontrados, output_dir)

        nao_encontrados_path = os.path.join(output_dir, "nao_encontrados.txt")
        with open(nao_encontrados_path, "w", encoding="utf-8") as f:
            for nome in nomes_nao_encontrados:
                f.write(nome + "\n")

        return jsonify({"status": "success", "message": "Processamento concluído!", "output_dir": output_dir})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
