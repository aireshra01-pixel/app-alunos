from flask import Flask, render_template, request, redirect, jsonify
import json
import os
import pickle


from googleapiclient.discovery import build

app = Flask(__name__)

# ================= GOOGLE CONFIG =================
SCOPES = ['https://www.googleapis.com/auth/documents',
          'https://www.googleapis.com/auth/drive']

PASTA_PRINCIPAL_ID = 'COLE_AQUI_O_ID_DA_PASTA'



import pickle
import base64

def autenticar_google():
    token_b64 = os.environ.get("GOOGLE_TOKEN")

    if not token_b64:
        raise Exception("GOOGLE_TOKEN não configurado")

    token_bytes = base64.b64decode(token_b64)
    creds = pickle.loads(token_bytes)

    return creds

    return creds

    # Salva o login
    with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

# Autentica
creds = autenticar_google()

# Serviços do Google
docs_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)
# ================= BANCO =================
def carregar_alunos():
    try:
        with open('alunos.json', 'r') as f:
            conteudo = f.read().strip()
            if not conteudo:
                return []
            return json.loads(conteudo)
    except:
        return []
    

def salvar_alunos(alunos):
    with open('alunos.json', 'w') as f:
        json.dump(alunos, f, indent=4)

# ================= CRIAR DOC =================
def criar_documento(nome, pasta_id):
    TEMPLATE_ID = '1hRCnVajmwIXcFKerPIWt_e5LoMZTLbK7e68tW7kBmdE'

    # 1️⃣ copia o template (vai pra raiz da service account)
    copia = drive_service.files().copy(
        fileId=TEMPLATE_ID,
        body={'name': nome},
        supportsAllDrives=True
    ).execute()

    file_id = copia.get('id')

    # 2️⃣ MOVE para a pasta correta (SEU DRIVE)
    drive_service.files().update(
        fileId=file_id,
        addParents=pasta_id,
        removeParents='root',
        supportsAllDrives=True
    ).execute()

    return file_id

def substituir_texto(doc_id, substituicoes):
    requests = []

    for chave, valor in substituicoes.items():
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': f'{{{{{chave}}}}}',
                    'matchCase': True
                },
                'replaceText': valor
            }
        })

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()


# ================= ADICIONAR TEXTO =================


# ================= ROTAS =================
@app.route('/')
def index():
    alunos = carregar_alunos()
    return render_template('index.html', alunos=alunos)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    alunos = carregar_alunos()

    PASTA_PRINCIPAL_ID = '1ju-tAf1Hfd7zTPylg9qYkrXfleNSGott'

    pasta = drive_service.files().create(
    body={
        'name': nome,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': ['1ju-tAf1Hfd7zTPylg9qYkrXfleNSGott']  # 👈 AQUI
    },
    fields='id'
    ).execute()

    alunos.append({
        'nome': nome,
        'pasta_id': pasta.get('id')
    })

    salvar_alunos(alunos)
    return redirect('/')


@app.route('/salvar', methods=['POST'])
def salvar():
    nome = request.form['aluno']
    alunos = carregar_alunos()
    aluno = next(a for a in alunos if a['nome'] == nome)

    compareceu = "Sim" if request.form.get('compareceu') else "Não"

    from datetime import datetime
    data_original = request.form['data']
    data_formatada = datetime.strptime(data_original, "%Y-%m-%d").strftime("%d/%m/%Y")


    def tratar(valor):
        if compareceu == "Não":
            return "-"
        return "Sim" if valor else "Não"

    doc_id = criar_documento(
        f"{nome} - {data_formatada}",
        aluno['pasta_id']
    )

    substituicoes = {
        'aluno': nome,
        'data': data_formatada,
        'horario': request.form['horario'],

        'compareceu': compareceu,
        'atrasou': tratar(request.form.get('atrasou')),
        'material': tratar(request.form.get('material')),
        'atividades': tratar(request.form.get('atividades')),

        'combinados': tratar(request.form.get('combinados')),
        'agitacao': tratar(request.form.get('agitacao')),
        'desregulacao': tratar(request.form.get('desregulacao')),
        'cansaco': tratar(request.form.get('cansaco')),

        'trabalhado': request.form['trabalhado'],
        'observacoes': request.form['observacoes'],
        'profissional': request.form['profissional']
    }

    substituir_texto(doc_id, substituicoes)

    return redirect('/')
# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)