# 🎓 HANDS-ON: CI/CD com SAST — SonarCloud + Trivy + GitHub Actions

**Guia prático para executar na live**

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter:

- [ ] Conta GitHub
- [ ] Conta SonarCloud (gratuita) — https://sonarcloud.io
- [ ] Git instalado localmente
- [ ] Docker Desktop instalado — https://www.docker.com/products/docker-desktop
- [ ] Editor de código (VS Code recomendado)

---

## 🚀 PARTE 1: Criar o Repositório no GitHub (5 min)

### Passo 1: Criar repositório

1. Acesse: **https://github.com/new**
2. **Repository name:** `fiap-demo-cicd-sast`
3. **Description:** `CI/CD com SAST — SonarCloud + Trivy + GitHub Actions`
4. **Visibilidade:** `Public` ← **obrigatório para SonarCloud gratuito!**
5. **NÃO marque** `Add a README file` ← vamos usar os arquivos já criados
6. Clique em: **"Create repository"**

### Passo 2: Inicializar o repositório local e fazer o primeiro push

No terminal, dentro da pasta do projeto:

```bash
git init
git add .
git commit -m "feat: estrutura inicial — app com vulnerabilidades e pipeline SAST"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/fiap-demo-cicd-sast.git
git push -u origin main
```

> ⚠️ Substitua `SEU-USUARIO` pelo seu usuário do GitHub.

---

## 🔐 PARTE 2: Configurar SonarCloud (10 min)

### Passo 1: Criar conta no SonarCloud

1. Acesse: **https://sonarcloud.io**
2. Clique em **"Log in with GitHub"**
3. Autorize o acesso ao GitHub
4. Selecione sua organização ou conta pessoal

### Passo 2: Adicionar o projeto

1. Clique em **"+"** (canto superior direito) → **"Analyze new project"**
2. Selecione o repositório `fiap-demo-cicd-sast`
3. Clique em **"Set Up"**
4. Em **"Choose your Analysis Method"** → selecione **"With GitHub Actions"

> ⚠️ O SonarCloud vai sugerir criar um arquivo `sonar-project.properties` — **ignore essa etapa**, o arquivo já está criado no repositório!

### Passo 3: Copiar o SONAR_TOKEN

1. O SonarCloud vai exibir o token gerado automaticamente
2. **Copie o token** — ele começa com `sqp_...`
3. **NÃO FECHE ESSA TELA AINDA**

### Passo 4: Adicionar o secret no GitHub

1. Abra uma nova aba: **seu repositório GitHub → Settings → Secrets and variables → Actions**
2. Clique em **"New repository secret"**
3. **Name:** `SONAR_TOKEN`
4. **Value:** Cole o token copiado
5. Clique em **"Add secret"**

### Passo 5: Copiar Organization Key e Project Key

De volta ao SonarCloud:
- **Organization Key:** aparece na URL após login (ex: `seu-usuario`)
- **Project Key:** aparece na tela de setup (ex: `seu-usuario_fiap-demo-cicd-sast`)

**📝 Anote esses dois valores — vamos usar no arquivo de configuração!**

### Passo 6: Atualizar o sonar-project.properties

Edite o arquivo `sonar-project.properties` na raiz do projeto e substitua os placeholders:

```properties
sonar.projectKey=seu-usuario_fiap-demo-cicd-sast
sonar.organization=seu-usuario
```

Depois faça o commit:

```bash
git add sonar-project.properties
git commit -m "config: adiciona Project Key e Organization Key do SonarCloud"
git push origin main
```

### ✅ Checklist SonarCloud:

```
✓ Conta criada e conectada ao GitHub
✓ Projeto fiap-demo-cicd-sast adicionado
✓ SONAR_TOKEN adicionado nos secrets do GitHub
✓ Organization Key anotado
✓ Project Key anotado
✓ sonar-project.properties atualizado e commitado
```

---

## 📁 PARTE 3: Estrutura do Projeto (já criada!)

Todos os arquivos já estão prontos no repositório. Confira a estrutura:

```
.
├── .github/
│   └── workflows/
│       └── sast-scan.yml      ← Pipeline GitHub Actions
├── app/
│   ├── app.py                 ← Flask com vulnerabilidades intencionais
│   ├── test_app.py            ← Testes unitários
│   ├── requirements.txt       ← Deps antigas (CVEs para Trivy)
│   └── Dockerfile             ← Imagem Docker
├── sonar-project.properties   ← ⚠️ Preencher com seus dados (Parte 2, Passo 6)
├── .gitignore
└── README.md
```

### 🔴 Vulnerabilidades intencionais no `app/app.py`

| # | Tipo | Linha | OWASP |
|---|------|-------|-------|
| 1 | SQL Injection | 12 | A03:2021 — Injection |
| 2 | Command Injection | 20 | A03:2021 — Injection |
| 3 | Hardcoded Secrets | 24-25 | A07:2021 — Auth Failures |
| 4 | debug=True em produção | 36 | A05:2021 — Misconfiguration |

> ⚠️ As versões em `app/requirements.txt` são intencionalmente antigas (`flask==2.0.1`, `cryptography==3.2`) — o Trivy vai detectar CVEs nelas!

---

## 🔄 PARTE 4: Pipeline GitHub Actions (já criada!)

O arquivo `.github/workflows/sast-scan.yml` já está no repositório com **3 jobs**:

```
Security Scan — SonarCloud + Trivy
├── 🔵 SonarCloud SAST          → roda em paralelo
├── 🔵 Trivy IaC + Dockerfile   → roda em paralelo
└── ⏳ Trivy Container Scan     → aguarda os dois anteriores
```

### O que cada job faz:

| Job | Ferramenta | O que analisa |
|-----|-----------|---------------|
| `sonarcloud` | SonarCloud | Código-fonte (SAST) + cobertura de testes |
| `trivy-iac` | Trivy | Dockerfile + arquivos de configuração |
| `trivy-container` | Trivy | Imagem Docker buildada (CVEs em pacotes) |

> A pipeline dispara automaticamente em **push para main** e em **Pull Requests**.

---

## 🚀 PARTE 5: Observar a Pipeline em Execução (10 min)

> O push já foi feito na Parte 1 — a pipeline já está rodando!

### Passo 1: Observar a pipeline executando

1. No GitHub: clique na aba **"Actions"**
2. Você verá o workflow **"Security Scan — SonarCloud + Trivy"** rodando
3. Clique nele para ver os jobs em tempo real:

```
Security Scan — SonarCloud + Trivy
├── 🟡 SonarCloud SAST          (rodando...)
├── 🟡 Trivy IaC + Dockerfile   (rodando...)
└── ⏳ Trivy Container Scan     (aguardando os anteriores)
```

### Passo 2: Ver resultados no SonarCloud

1. Acesse: **https://sonarcloud.io**
2. Clique no projeto `fiap-demo-cicd-sast`
3. Veja o dashboard com as vulnerabilidades detectadas:

```
🔴 Quality Gate: FAILED

Vulnerabilities: 3
├── SQL Injection (app.py:12)
├── Command Injection (app.py:20)
└── Hardcoded credentials (app.py:23)

Coverage: ~45%  ← abaixo do mínimo
```

### Passo 3: Ver resultados do Trivy no GitHub Security

1. No GitHub: aba **"Security"** → **"Code scanning alerts"**
2. Você verá os CVEs das dependências antigas e problemas no Dockerfile

---

## 🔍 PARTE 6: Criar PR e Ver o Fluxo Completo (10 min)

### Passo 1: Criar branch de feature

```bash
git checkout -b feature/add-new-route
```

### Passo 2: Adicionar mais uma vulnerabilidade

Adicione ao final do `app/app.py`:

```python
# ❌ VULNERABILIDADE 4: Path Traversal
@app.route('/file')
def read_file():
    filename = request.args.get('name')
    with open(f"/var/data/{filename}", 'r') as f:
        return f.read()
```

### Passo 3: Commit e push

```bash
git add app/app.py
git commit -m "feat: adiciona rota de leitura de arquivo"
git push origin feature/add-new-route
```

### Passo 4: Abrir Pull Request

1. No GitHub: clique em **"Compare & pull request"** (banner amarelo que aparece automaticamente)
2. **Title:** `feat: adiciona rota de leitura de arquivo`
3. Clique em **"Create pull request"**

### Passo 5: Observar o comportamento

✅ A pipeline de SAST executa automaticamente no PR  
✅ O SonarCloud comenta no PR com os problemas encontrados  
✅ O status check aparece como ❌ (Quality Gate falhou)  
✅ O merge fica bloqueado visualmente  

> 💡 **Momento de ouro da live:** mostrar o PR bloqueado e explicar que nenhum código inseguro entra na `main` sem revisão!  

---

## ✅ PARTE 7: Corrigir as Vulnerabilidades (10 min)

### Passo 1: Corrigir o `app/app.py`

Substitua o conteúdo do arquivo pela versão corrigida:

```python
from flask import Flask, request
import sqlite3
import subprocess
import os

app = Flask(__name__)

# ✅ Fix 1: SQL com parâmetros (sem SQL Injection)
@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    conn = sqlite3.connect('users.db')
    result = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchall()
    return str(result)

# ✅ Fix 2: Sem shell=True (sem Command Injection)
@app.route('/ping')
def ping():
    host = request.args.get('host')
    output = subprocess.check_output(["ping", "-c", "1", host])
    return output

# ✅ Fix 3: Secrets via variáveis de ambiente
SECRET_KEY = os.environ.get("SECRET_KEY")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

@app.route('/user/safe')
def get_user_safe():
    user_id = request.args.get('id')
    conn = sqlite3.connect('users.db')
    result = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchall()
    return str(result)

# ✅ Fix 4: Sem Path Traversal — valida o nome do arquivo
ALLOWED_FILES = {"report.txt", "status.txt"}

@app.route('/file')
def read_file():
    filename = request.args.get('name')
    if filename not in ALLOWED_FILES:
        return "File not allowed", 403
    filepath = os.path.join("/var/data", filename)
    with open(filepath, 'r') as f:
        return f.read()

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
```

### Passo 2: Atualizar dependências vulneráveis

Substitua o conteúdo de `app/requirements.txt`:

```
flask==3.0.0
requests==2.31.0
pyyaml==6.0.1
cryptography==41.0.6
pytest==7.0.0
pytest-cov==4.0.0
```

### Passo 3: Commit e push

```bash
git add .
git commit -m "fix: corrige SQL injection, command injection, hardcoded secrets e path traversal"
git push origin feature/add-new-route
```

### Passo 4: Observar a pipeline re-executar

1. Vá para a aba **"Actions"** no GitHub
2. Veja a nova execução rodando no mesmo PR
3. Aguarde ~2 minutos

### Passo 5: Ver o Quality Gate passar

No SonarCloud:
```
✅ Quality Gate: PASSED

Vulnerabilities: 0
Bugs: 0
Coverage: 78%
```

No GitHub, o PR agora mostra:
```
✅ SonarCloud SAST — Passed
✅ Trivy IaC — Passed
✅ Trivy Container — Passed
→ Merge liberado!
```

### Passo 6: Fazer o Merge

1. Clique em **"Merge pull request"**
2. Clique em **"Confirm merge"**

🎉 **Código seguro entrou na main!**

---

## 📊 PARTE 8: Explorar o Dashboard do SonarCloud (5 min)

Acesse **https://sonarcloud.io** → seu projeto e explore:

### Overview
- **Quality Gate:** status atual
- **Bugs / Vulnerabilities / Code Smells:** contadores
- **Coverage:** percentual de cobertura de testes
- **Duplications:** código duplicado

### Security
- Lista de vulnerabilidades com:
  - Arquivo e linha exata
  - Categoria OWASP
  - Sugestão de correção
  - Status (Open / Fixed / Accepted)

### Activity
- Histórico de análises ao longo do tempo
- Evolução das métricas

### Pull Requests
- Análise específica de cada PR
- Comparação com a branch main

---

## 🐛 Troubleshooting Comum

### SonarCloud não analisa — "Project not found"
**Solução:** Verificar se o `sonar.projectKey` e `sonar.organization` no `sonar-project.properties` estão corretos — copiar exatamente do SonarCloud, sem espaços extras.

### SONAR_TOKEN inválido
**Solução:** Gerar novo token em SonarCloud → **My Account → Security → Generate Token**. Atualizar o secret no GitHub.

### Pipeline não executa no PR
**Solução:** Verificar se o arquivo está em `.github/workflows/` (com o ponto no início). O diretório `.github` é oculto — use `ls -la` para confirmar.

### Trivy não encontra vulnerabilidades no container
**Solução:** Confirme que o `app/requirements.txt` contém as versões antigas (`flask==2.0.1`, `cryptography==3.2`). Essas versões são intencionais para a demo.

### Coverage aparece como 0% no SonarCloud
**Solução:** Verificar se o `coverage.xml` está sendo gerado e se o caminho no `sonar-project.properties` está correto (`sonar.python.coverage.reportPaths=coverage.xml`). O arquivo é gerado na raiz do projeto.

### Quality Gate não bloqueia o merge
**Solução:** Configurar Branch Protection no GitHub:
1. **Settings → Branches → Add branch protection rule**
2. Branch name pattern: `main`
3. Marque: ✅ `Require status checks to pass before merging`
4. Busque e adicione: `SonarCloud Code Analysis`
5. Clique em **"Save changes"**

### Erro de permissão no upload do SARIF
**Solução:** Verificar se o repositório é público. Para repositórios privados, é necessário GitHub Advanced Security habilitado.

---

## 📚 Recursos Adicionais

- **SonarCloud:** https://sonarcloud.io
- **Trivy Docs:** https://aquasecurity.github.io/trivy/
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **GitHub Actions:** https://docs.github.com/en/actions
- **SonarCloud GitHub Action:** https://github.com/SonarSource/sonarcloud-github-action

---

**Professor:** José Neto  
**Curso:** DevOps e Arquitetura Cloud — FIAP  
**Tema:** CI/CD com SAST — SonarCloud + Trivy + GitHub Actions

---

**🔐 Secure by Default. Shift Left. Ship Fast.**
