from flask import Flask, render_template, request, send_file
import pandas as pd
from fpdf import FPDF
from io import StringIO, BytesIO

app = Flask(__name__)

def limpar_lista(texto, nome_prefixo):
    """
    Recebe o texto colado (Ctrl+C -> Ctrl+V),
    extrai Objeto, Endereço e CEP
    """
    linhas = texto.strip().splitlines()
    dados = []

    for linha in linhas:
        # tenta separar por TAB primeiro
        partes = linha.split("\t")
        if len(partes) < 3:
            # se não tinha TAB, separa por múltiplos espaços
            partes = [p for p in linha.split(" ") if p.strip()]

        if len(partes) >= 6:
            objeto = partes[1].strip()
            endereco = partes[3].strip()
            cep = partes[5].strip()
            dados.append([objeto, endereco, cep])

    df = pd.DataFrame(dados, columns=[f"objeto_{nome_prefixo}", f"endereco_{nome_prefixo}", f"cep_{nome_prefixo}"])

    # Normalização
    df[f"endereco_{nome_prefixo}"] = df[f"endereco_{nome_prefixo}"].fillna("").str.strip().str.upper()
    df[f"cep_{nome_prefixo}"] = df[f"cep_{nome_prefixo}"].fillna("").astype(str).str.strip()

    return df

def gerar_pdf(coincidentes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Endereços Coincidentes", ln=True, align="C")
    pdf.ln(10)

    # Cabeçalho
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(60, 10, "Objeto", border=1)
    pdf.cell(90, 10, "Endereço", border=1)
    pdf.cell(40, 10, "CEP", border=1)
    pdf.ln()

    # Conteúdo
    pdf.set_font("Arial", size=10)
    for _, row in coincidentes.iterrows():
        pdf.cell(60, 10, str(row.iloc[0]), border=1)
        pdf.cell(90, 10, str(row.iloc[1])[:40], border=1)
        pdf.cell(40, 10, str(row.iloc[2]), border=1)
        pdf.ln()

    # Retornar PDF em memória
    pdf_buffer = BytesIO()
    pdf_output = pdf.output(dest="S").encode("latin1")
    pdf_buffer.write(pdf_output)
    pdf_buffer.seek(0)
    return pdf_buffer


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        lista1 = request.form.get("lista1", "")
        lista2 = request.form.get("lista2", "")

        df1 = limpar_lista(lista1, "1")
        df2 = limpar_lista(lista2, "2")

        enderecos_lista1 = set(zip(df1["endereco_1"], df1["cep_1"]))
        df2["match"] = df2.apply(lambda row: (row["endereco_2"], row["cep_2"]) in enderecos_lista1, axis=1)

        coincidentes = df2[df2["match"]][["objeto_2", "endereco_2", "cep_2"]]

        pdf_buffer = gerar_pdf(coincidentes)
        return send_file(pdf_buffer, as_attachment=True, download_name="enderecos_coincidentes.pdf", mimetype="application/pdf")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
