from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import PyPDF2
import zipfile

temp_folder = 'temp_files'
output_folder = 'output_pdfs'

app = Flask(__name__)
app.secret_key = 'segredo'  # Necessário para flash messages

# Garante que as pastas existem
os.makedirs(temp_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Função para buscar nomes no PDF
def buscar_nome_pdf(pdf_file_path, nome):
    found_pages = []
    with open(pdf_file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and nome in text:
                found_pages.append(page_num)
    return found_pages

# Função para salvar PDFs individuais
def salvar_pdfs(pdf_file_path, nome, paginas_encontradas, output_dir):
    with open(pdf_file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        
        for pagina in paginas_encontradas:
            writer.add_page(reader.pages[pagina])

        output_file_path = os.path.join(output_dir, f'{nome}.pdf')
        with open(output_file_path, 'wb') as output_file:
            writer.write(output_file)

# Processamento do PDF
def processar_pdf(pdf_path, nomes):
    nao_encontrados = []
    
    for nome in nomes:
        paginas_encontradas = buscar_nome_pdf(pdf_path, nome)
        if paginas_encontradas:
            salvar_pdfs(pdf_path, nome, paginas_encontradas, output_folder)
        else:
            nao_encontrados.append(nome)
    
    # Criar arquivo ZIP
    zip_path = os.path.join(temp_folder, 'pdfs_resultados.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_name in os.listdir(output_folder):
            file_path = os.path.join(output_folder, file_name)
            zipf.write(file_path, file_name)
    
    # Remover arquivos processados (LGPD Compliance)
    for file_name in os.listdir(output_folder):
        os.remove(os.path.join(output_folder, file_name))
    
    return zip_path, nao_encontrados

# Rota principal
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files or 'names_file' not in request.files:
            flash("Erro: Você deve enviar um arquivo PDF e uma lista de nomes.", "danger")
            return redirect(url_for('index'))
        
        pdf_file = request.files['pdf_file']
        names_file = request.files['names_file']
        
        if not pdf_file or not names_file:
            flash("Erro: Arquivos inválidos!", "danger")
            return redirect(url_for('index'))
        
        pdf_path = os.path.join(temp_folder, pdf_file.filename)
        pdf_file.save(pdf_path)
        
        # Lendo os nomes enviados
        nomes = names_file.read().decode('utf-8').splitlines()
        zip_path, nao_encontrados = processar_pdf(pdf_path, nomes)
        
        # Remover o PDF original (LGPD Compliance)
        os.remove(pdf_path)

        flash("Processamento concluído! Clique abaixo para baixar os arquivos.", "success")
        return redirect(url_for('download', filename='pdfs_resultados.zip'))
    
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(temp_folder, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
