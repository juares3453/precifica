from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from dotenv import load_dotenv

import os

load_dotenv()

app = Flask(__name__)
# Configurando o SQLAlchemy para PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SECRET_KEY"] = os.getenv("SESSION_KEY")  # Para utilizar mensagens flash
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Tempo de expiração da sessão de 1 hora
db = SQLAlchemy(app)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Função para criar um usuário inicial
def criar_usuario_inicial():
    """
    Cria ou atualiza o usuário inicial no banco de dados.
    """
    username = os.getenv("USER")
    password = os.getenv("PASSWORD")

    usuario_existente = Usuario.query.filter_by(username=username).first()
    if usuario_existente:
        usuario_existente.set_password(password)
        db.session.commit()
        print(f"Usuário '{username}' atualizado com nova senha.")
    else:
        novo_usuario = Usuario(username=username)
        novo_usuario.set_password(password)
        db.session.add(novo_usuario)
        db.session.commit()
        print(f"Usuário '{username}' criado com sucesso.")

# Inicializando o banco de dados e criando um usuário inicial, se necessário
with app.app_context():
    db.create_all()
    criar_usuario_inicial()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("login"))
        session.modified = True  # Atualiza o tempo da sessão a cada requisição
        return f(*args, **kwargs)
    return decorated_function


def calcular_precificacao(custo_material, custo_mao_obra, margem_lucro, outros_custos=0):
    """
    Calcula o preço final baseado nos custos e na margem de lucro.
    :param custo_material: Custo dos materiais utilizados.
    :param custo_mao_obra: Custo da mão de obra.
    :param margem_lucro: Percentual de margem de lucro desejada (ex.: 20 para 20%).
    :param outros_custos: Outros custos adicionais.
    :return: Preço final.
    """
    custo_total = custo_material + custo_mao_obra + outros_custos
    lucro = custo_total * (margem_lucro / 100)
    preco_final = custo_total + lucro
    return round(preco_final, 2)

# Rotas
@app.route("/")
@login_required
def home():
    return redirect(url_for("calcular"))


@app.route("/calcular")
@login_required
def modulos():
    """
    Tela inicial para escolher os módulos do sistema.
    """
    return render_template("calcular.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session.permanent = True  # Configura a sessão como permanente para respeitar a expiração configurada
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("modulos"))
        else:
            flash("Nome de usuário ou senha incorretos.", "error")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for("login"))

@app.route('/calcular', methods=['GET', 'POST'])
@login_required
def calcular():
    if request.method == 'POST':
        try:
            # Pegando os dados do formulário
            custo_material = float(request.form['custo_material'])
            custo_mao_obra = float(request.form['custo_mao_obra'])
            margem_lucro = float(request.form['margem_lucro'])
            outros_custos = float(request.form.get('outros_custos', 0))

            # Chamando a função de cálculo
            preco_final = calcular_precificacao(custo_material, custo_mao_obra, margem_lucro, outros_custos)

            return render_template('resultado.html', preco_final=preco_final)
        except ValueError:
            flash("Por favor, insira valores válidos!", "error")
            return redirect(url_for('calcular'))

    return render_template('calcular.html')

if __name__ == "__main__":
    app.run(debug=True)
