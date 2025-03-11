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


class Mercadoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    quantidade = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(200))
    preco = db.Column(db.Float)

    def __repr__(self):
        return f"<Mercadoria {self.nome}>"


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Fornecedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), nullable=False, unique=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Fornecedor {self.nome}>'


class NotaFiscal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_nf = db.Column(db.String(20), nullable=False, unique=True)
    data_emissao = db.Column(db.Date, nullable=False)
    data_entrega = db.Column(db.Date, nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=False)
    
    fornecedor = db.relationship('Fornecedor', backref=db.backref('notas_fiscais', lazy=True))

    def __repr__(self):
        return f'<NotaFiscal {self.numero_nf}>'


class ItemNotaFiscal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    grupo = db.Column(db.String(50), nullable=True)  # Adicionando a coluna grupo
    nota_fiscal_id = db.Column(db.Integer, db.ForeignKey('nota_fiscal.id'), nullable=False)

    nota_fiscal = db.relationship('NotaFiscal', backref=db.backref('itens', lazy=True))

    def __repr__(self):
        return f'<ItemNotaFiscal {self.descricao}>'


class LogMovimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    acao = db.Column(db.String(100), nullable=False)
    mercadoria_id = db.Column(db.Integer, db.ForeignKey("mercadoria.id"), nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedor.id"), nullable=True)
    descricao = db.Column(db.String(200), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", backref=db.backref("logs", lazy=True))
    mercadoria = db.relationship("Mercadoria", backref=db.backref("logs", lazy=True))
    fornecedor = db.relationship("Fornecedor", backref=db.backref("logs", lazy=True))

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente = db.Column(db.String(100), nullable=False)
    profissional = db.Column(db.String(100), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    observacoes = db.Column(db.String(200))

    def to_dict(self):
        return {
            "title": f"{self.paciente} ({self.profissional})",
            "start": self.data_hora_inicio.isoformat(),
            "end": self.data_hora_fim.isoformat(),
            "description": self.observacoes,
        }

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    apelido = db.Column(db.String(100))
    nascimento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100))
    celular = db.Column(db.String(15))
    rg = db.Column(db.String(20))
    cpf = db.Column(db.String(20))
    estado_civil = db.Column(db.String(20))
    escolaridade = db.Column(db.String(50))
    observacoes = db.Column(db.String(200))

    def __repr__(self):
        return f'<Paciente {self.nome}>'

class Profissional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    nascimento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    cor = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    estado_civil = db.Column(db.String(20), nullable=False)
    cro = db.Column(db.String(20), nullable=False)
    usuario = db.Column(db.String(50))
    rg = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Profissional {self.nome}>'

class Odontograma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    dente = db.Column(db.String(10), nullable=False)  # Ex: 11, 21, 36
    status = db.Column(db.String(100), nullable=False)  # Ex: "Cariado", "Ausente", "Tratado"
    observacoes = db.Column(db.String(200))

    paciente = db.relationship('Paciente', backref=db.backref('odontograma', lazy=True))

class Procedimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(200), nullable=True)
    preco = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Procedimento {self.nome}>"

class ItemOrcamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    dente = db.Column(db.String(10), nullable=False)
    procedimento_id = db.Column(db.Integer, db.ForeignKey('procedimento.id'), nullable=False)
    observacoes = db.Column(db.String(200), nullable=True)
    preco = db.Column(db.Float, nullable=False)

    paciente = db.relationship('Paciente', backref=db.backref('orcamentos', lazy=True))
    procedimento = db.relationship('Procedimento', backref=db.backref('itens_orcamento', lazy=True))


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


def registrar_log(acao, descricao, mercadoria_id=None, fornecedor_id=None):
    log = LogMovimentacao(
        usuario_id=session.get("user_id"),
        acao=acao,
        mercadoria_id=mercadoria_id,
        fornecedor_id=fornecedor_id,
        descricao=descricao,
    )
    db.session.add(log)
    db.session.commit()

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
    """
    Redireciona para a tela de módulos ao acessar a rota principal.
    """
    return redirect(url_for("modulos"))


@app.route("/modulos")
@login_required
def modulos():
    """
    Tela inicial para escolher os módulos do sistema.
    """
    return render_template("modulos.html")


@app.route("/estoque")
@login_required
def estoque():
    """
    Tela de estoque de mercadorias.
    """
    mercadorias = Mercadoria.query.all()
    return render_template("estoque.html", mercadorias=mercadorias)

@app.route('/api/agendamentos')
@login_required
def api_agendamentos():
    """
    Retorna os agendamentos no formato esperado pelo FullCalendar.
    """
    agendamentos = Agendamento.query.all()  # Busca todos os agendamentos
    eventos = [
        {
            "title": f"{agendamento.paciente} ({agendamento.profissional})",
            "start": agendamento.data_hora_inicio.isoformat(),
            "end": agendamento.data_hora_fim.isoformat(),
            "description": agendamento.observacoes
        }
        for agendamento in agendamentos
    ]
    return jsonify(eventos)

@app.route('/api/agendamentos/novo', methods=['POST'])
@login_required
def criar_agendamento():
    """
    API endpoint to create a new event.
    """
    data = request.get_json()
    try:
        novo_agendamento = Agendamento(
            paciente=data['paciente'],
            profissional=data['profissional'],
            data_hora_inicio=datetime.fromisoformat(data['start']),
            data_hora_fim=datetime.fromisoformat(data['end']),
            observacoes=data.get('observacoes', '')
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Agendamento criado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/api/agendamentos/editar/<int:id>', methods=['PUT'])
@login_required
def editar_agendamento(id):
    """
    API endpoint to update an event.
    """
    data = request.get_json()
    agendamento = Agendamento.query.get_or_404(id)
    try:
        agendamento.paciente = data.get('paciente', agendamento.paciente)
        agendamento.profissional = data.get('profissional', agendamento.profissional)
        agendamento.data_hora_inicio = datetime.fromisoformat(data.get('start', agendamento.data_hora_inicio.isoformat()))
        agendamento.data_hora_fim = datetime.fromisoformat(data.get('end', agendamento.data_hora_fim.isoformat()))
        agendamento.observacoes = data.get('observacoes', agendamento.observacoes)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Agendamento atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/api/agendamentos/excluir/<int:id>', methods=['DELETE'])
@login_required
def excluir_agendamento_api(id):
    """
    API endpoint to delete an event.
    """
    agendamento = Agendamento.query.get_or_404(id)
    try:
        db.session.delete(agendamento)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Agendamento excluído com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/agendamentos/calendario')
@login_required
def calendario():
    return render_template('calendario.html')

@app.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar():
    if request.method == "POST":
        nome = request.form["nome"].strip().lower()
        quantidade = int(request.form["quantidade"])
        descricao = request.form["descricao"]
        preco = float(request.form["preco"])

        mercadoria_existente = Mercadoria.query.filter(
            db.func.lower(Mercadoria.nome) == nome
        ).first()
        if mercadoria_existente:
            flash("Já existe uma mercadoria com esse nome!", "error")
            return redirect(url_for("adicionar"))

        nova_mercadoria = Mercadoria(
            nome=nome, quantidade=quantidade, descricao=descricao, preco=preco
        )
        db.session.add(nova_mercadoria)
        db.session.commit()
        registrar_log(
            "Inserção",
            f"Mercadoria '{nova_mercadoria.nome}' adicionada com quantidade {quantidade}.",
            mercadoria_id=nova_mercadoria.id,
        )
        flash("Mercadoria adicionada com sucesso!", "success")
        return redirect(url_for("estoque"))

    return render_template("adicionar.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    mercadoria = Mercadoria.query.get_or_404(id)
    if request.method == "POST":
        mercadoria.nome = request.form["nome"].strip().lower()
        mercadoria.quantidade = int(request.form["quantidade"])
        mercadoria.descricao = request.form["descricao"]
        mercadoria.preco = float(request.form["preco"])
        db.session.commit()
        registrar_log(
            "Edição",
            f"Mercadoria '{mercadoria.nome}' editada. Quantidade: {mercadoria.quantidade}.",
            mercadoria_id=mercadoria.id,
        )
        flash("Mercadoria editada com sucesso!", "success")
        return redirect(url_for("index"))

    return render_template("editar.html", mercadoria=mercadoria)


@app.route("/excluir/<int:id>")
@login_required
def excluir(id):
    # Tenta buscar a mercadoria antes de excluí-la
    mercadoria = Mercadoria.query.get(id)
    
    if not mercadoria:
        flash("Mercadoria não encontrada.", "error")
        return redirect(url_for("index"))

    try:
        # Registrar o log antes de excluir a mercadoria
        registrar_log(
            acao="Exclusão",
            descricao=f"Mercadoria '{mercadoria.nome}' excluída.",
            mercadoria_id=mercadoria.id
        )

        # Agora exclui a mercadoria
        db.session.delete(mercadoria)
        db.session.commit()
        flash("Mercadoria excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir mercadoria: {str(e)}", "error")
    
    return redirect(url_for("index"))

@app.route("/buscar_ajax", methods=["GET"])
@login_required
def buscar_ajax():
    query = request.args.get("query", "").strip().lower()
    resultados = Mercadoria.query.filter(Mercadoria.nome.like(f"%{query}%")).all()
    mercadorias = [
        {
            "id": mercadoria.id,
            "nome": mercadoria.nome,
            "quantidade": mercadoria.quantidade,
            "descricao": mercadoria.descricao,
            "preco": mercadoria.preco,
        }
        for mercadoria in resultados
    ]
    return jsonify(mercadorias)

@app.route("/movimentacoes")
@login_required
def movimentacoes():
    logs = LogMovimentacao.query.order_by(LogMovimentacao.data_hora.desc()).all()
    return render_template("movimentacoes.html", logs=logs)

@app.route("/fornecedores", methods=["GET", "POST"])
@login_required
def gerenciar_fornecedores():
    fornecedor_id = request.args.get('fornecedor_id')
    fornecedor = Fornecedor.query.get(fornecedor_id) if fornecedor_id else None

    if request.method == 'POST':
        cnpj = request.form['cnpj']
        nome = request.form['nome']
        endereco = request.form['endereco']
        telefone = request.form['telefone']
        email = request.form['email']

        if fornecedor:  # Editando fornecedor
            fornecedor_existente = Fornecedor.query.filter(
                Fornecedor.cnpj == cnpj, 
                Fornecedor.id != fornecedor.id
            ).first()
            if fornecedor_existente:
                flash('Já existe um fornecedor com esse CNPJ!', 'error')
                return redirect(url_for('gerenciar_fornecedores', fornecedor_id=fornecedor.id))

            fornecedor.cnpj = cnpj
            fornecedor.nome = nome
            fornecedor.endereco = endereco
            fornecedor.telefone = telefone
            fornecedor.email = email
            db.session.commit()
            registrar_log(
                "Edição Fornecedor",
                f"Fornecedor '{fornecedor.nome}' editado.",
                fornecedor_id=fornecedor.id,
            )
            flash('Fornecedor editado com sucesso!', 'success')
        else:  # Novo fornecedor
            fornecedor_existente = Fornecedor.query.filter_by(cnpj=cnpj).first()
            if fornecedor_existente:
                flash('Já existe um fornecedor com esse CNPJ!', 'error')
                return redirect(url_for('gerenciar_fornecedores'))

            novo_fornecedor = Fornecedor(
                cnpj=cnpj, 
                nome=nome, 
                endereco=endereco, 
                telefone=telefone, 
                email=email
            )
            db.session.add(novo_fornecedor)
            db.session.commit()
            registrar_log(
                "Inserção Fornecedor",
                f"Fornecedor '{novo_fornecedor.nome}' adicionado.",
                fornecedor_id=novo_fornecedor.id,
            )
            flash('Fornecedor adicionado com sucesso!', 'success')

        return redirect(url_for('gerenciar_fornecedores'))

    fornecedores = Fornecedor.query.all()
    return render_template('fornecedor.html', fornecedores=fornecedores, fornecedor=fornecedor)

@app.route('/excluir_fornecedor/<int:id>')
@login_required
def excluir_fornecedor(id):
    fornecedor = Fornecedor.query.get(id)
    
    if not fornecedor:
        flash("Fornecedor não encontrado.", "error")
        return redirect(url_for('gerenciar_fornecedores'))

    # Verificar se existem notas fiscais associadas
    notas_associadas = NotaFiscal.query.filter_by(fornecedor_id=fornecedor.id).all()
    if notas_associadas:
        flash("Não é possível excluir o fornecedor, pois existem notas fiscais associadas.", "error")
        return redirect(url_for('gerenciar_fornecedores'))

    try:
        registrar_log(
            acao="Exclusão Fornecedor",
            descricao=f"Fornecedor '{fornecedor.nome}' excluído.",
            fornecedor_id=fornecedor.id
        )

        # Agora exclui o fornecedor
        db.session.delete(fornecedor)
        db.session.commit()
        flash('Fornecedor excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir fornecedor: {str(e)}", "error")
    
    return redirect(url_for('gerenciar_fornecedores'))

@app.route("/fornecedores/<int:fornecedor_id>/nova_nf", methods=["GET", "POST"])
@login_required
def criar_nota_fiscal(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)

    if request.method == "POST":
        numero_nf = request.form['numero_nf']
        data_emissao = request.form['data_emissao']
        data_entrega = request.form['data_entrega']

        # Validação básica para garantir que todos os campos foram preenchidos
        if not numero_nf or not data_emissao or not data_entrega:
            flash("Todos os campos são obrigatórios!", "error")
            return redirect(url_for('criar_nota_fiscal', fornecedor_id=fornecedor.id))

        try:
            # Verificar se já existe uma NF com o mesmo número
            nota_existente = NotaFiscal.query.filter_by(numero_nf=numero_nf).first()
            if nota_existente:
                flash('Já existe uma Nota Fiscal com esse número!', 'error')
                return redirect(url_for('criar_nota_fiscal', fornecedor_id=fornecedor.id))

            # Criar a nova Nota Fiscal
            nova_nf = NotaFiscal(
                numero_nf=numero_nf,
                data_emissao=datetime.strptime(data_emissao, "%Y-%m-%d").date(),
                data_entrega=datetime.strptime(data_entrega, "%Y-%m-%d").date(),
                fornecedor_id=fornecedor.id
            )

            db.session.add(nova_nf)
            db.session.commit()
            flash('Nota Fiscal criada com sucesso!', 'success')
            return redirect(url_for('listar_notas_fiscais', fornecedor_id=fornecedor.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar Nota Fiscal: {str(e)}", "error")
            return redirect(url_for('criar_nota_fiscal', fornecedor_id=fornecedor.id))

    return render_template("nova_nf.html", fornecedor=fornecedor)

@app.route("/fornecedores/<int:fornecedor_id>/nfs")
@login_required
def listar_notas_fiscais(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    notas_fiscais = NotaFiscal.query.filter_by(fornecedor_id=fornecedor.id).all()
    return render_template("listar_nfs.html", fornecedor=fornecedor, notas_fiscais=notas_fiscais)

@app.route("/nota_fiscal/<int:nf_id>", methods=["GET", "POST"])
@login_required
def detalhar_nota_fiscal(nf_id):
    nota_fiscal = NotaFiscal.query.get_or_404(nf_id)

    if request.method == "POST":
        descricao = request.form['descricao']
        quantidade = int(request.form['quantidade'])
        preco_unitario = float(request.form['preco_unitario'])
        grupo = request.form['grupo']  # Novo campo do grupo

        novo_item = ItemNotaFiscal(
            descricao=descricao,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            grupo=grupo,  # Armazena o grupo selecionado
            nota_fiscal_id=nota_fiscal.id
        )
        try:
            db.session.add(novo_item)
            db.session.commit()
            flash('Item adicionado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao adicionar item: {str(e)}", "error")

    return render_template("detalhar_nf.html", nota_fiscal=nota_fiscal)

@app.route("/nota_fiscal/<int:nf_id>/editar", methods=["GET", "POST"])
@login_required
def editar_nota_fiscal(nf_id):
    nota_fiscal = NotaFiscal.query.get_or_404(nf_id)

    if request.method == "POST":
        # Lógica de edição da Nota Fiscal
        nota_fiscal.numero_nf = request.form["numero_nf"]
        nota_fiscal.data_emissao = request.form["data_emissao"]
        nota_fiscal.data_entrega = request.form["data_entrega"]
        db.session.commit()
        flash("Nota Fiscal editada com sucesso!", "success")
        return redirect(url_for("listar_notas_fiscais", fornecedor_id=nota_fiscal.fornecedor_id))

    return render_template("editar_nf.html", nota_fiscal=nota_fiscal)

@app.route("/nota_fiscal/<int:nf_id>/excluir", methods=["POST"])
@login_required
def excluir_nota_fiscal(nf_id):
    nota_fiscal = NotaFiscal.query.get_or_404(nf_id)
    try:
        db.session.delete(nota_fiscal)
        db.session.commit()
        flash("Nota Fiscal excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir Nota Fiscal: {str(e)}", "error")

    return redirect(url_for("listar_notas_fiscais", fornecedor_id=nota_fiscal.fornecedor_id))

@app.route("/nota_fiscal/<int:nf_id>/item/<int:item_id>/editar", methods=["GET", "POST"])
@login_required
def editar_item_nf(nf_id, item_id):
    nota_fiscal = NotaFiscal.query.get_or_404(nf_id)
    item = ItemNotaFiscal.query.get_or_404(item_id)

    if request.method == "POST":
        item.descricao = request.form['descricao']
        item.quantidade = int(request.form['quantidade'])
        item.preco_unitario = float(request.form['preco_unitario'])

        try:
            db.session.commit()
            flash('Item da Nota Fiscal editado com sucesso!', 'success')
            return redirect(url_for('detalhar_nota_fiscal', nf_id=nota_fiscal.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao editar item: {str(e)}", "error")
            return redirect(url_for('editar_item_nf', nf_id=nota_fiscal.id, item_id=item.id))

    return render_template("editar_item_nf.html", nota_fiscal=nota_fiscal, item=item)

@app.route("/nota_fiscal/<int:nf_id>/item/<int:item_id>/excluir", methods=["POST"])
@login_required
def excluir_item_nf(nf_id, item_id):
    item = ItemNotaFiscal.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item da Nota Fiscal excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir item: {str(e)}", "error")
    return redirect(url_for('detalhar_nota_fiscal', nf_id=nf_id))

@app.route('/pacientes/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_paciente():
    if request.method == 'POST':
        # Capturar os dados do formulário
        nome = request.form['nome']
        apelido = request.form.get('apelido')
        nascimento = request.form['nascimento']
        sexo = request.form['sexo']
        email = request.form.get('email', None) if 'sem_email' not in request.form else None
        celular = request.form.get('celular')
        rg = request.form.get('rg')
        cpf = request.form.get('cpf')
        estado_civil = request.form.get('estado_civil')
        escolaridade = request.form.get('escolaridade')
        observacoes = request.form.get('observacoes')

        # Salvar os dados no banco
        novo_paciente = Paciente(
            nome=nome,
            apelido=apelido,
            nascimento=datetime.strptime(nascimento, "%Y-%m-%d"),
            sexo=sexo,
            email=email,
            celular=celular,
            rg=rg,
            cpf=cpf,
            estado_civil=estado_civil,
            escolaridade=escolaridade,
            observacoes=observacoes
        )
        db.session.add(novo_paciente)
        db.session.commit()

        flash("Paciente cadastrado com sucesso!", "success")
        return redirect(url_for('listar_pacientes'))

    return render_template('cadastro_paciente.html')

@app.route('/profissionais/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_profissional():
    if request.method == 'POST':
        nome = request.form['nome']
        nascimento = request.form['nascimento']
        sexo = request.form['sexo']
        cor = request.form['cor']
        email = request.form['email']
        estado_civil = request.form['estado_civil']
        cro = request.form['cro']
        usuario = request.form.get('usuario')
        rg = request.form['rg']
        cpf = request.form['cpf']

        # Salvar no banco de dados
        novo_profissional = Profissional(
            nome=nome,
            nascimento=datetime.strptime(nascimento, "%Y-%m-%d"),
            sexo=sexo,
            cor=cor,
            email=email,
            estado_civil=estado_civil,
            cro=cro,
            usuario=usuario,
            rg=rg,
            cpf=cpf
        )
        db.session.add(novo_profissional)
        db.session.commit()

        flash("Profissional cadastrado com sucesso!", "success")
        return redirect(url_for('modulos'))

    return render_template('cadastro_profissional.html')

@app.route('/pacientes', methods=['GET'])
@login_required
def listar_pacientes():
    query = request.args.get('query', '')
    if query:
        pacientes = Paciente.query.filter(Paciente.nome.ilike(f'%{query}%')).all()
    else:
        pacientes = Paciente.query.all()
    return render_template('listar_pacientes.html', pacientes=pacientes, query=query)

@app.route('/profissionais', methods=['GET'])
@login_required
def listar_profissionais():
    query = request.args.get('query', '')
    if query:
        profissionais = Profissional.query.filter(Profissional.nome.ilike(f'%{query}%')).all()
    else:
        profissionais = Profissional.query.all()
    return render_template('listar_profissionais.html', profissionais=profissionais, query=query)

@app.route('/pacientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    if request.method == 'POST':
        paciente.nome = request.form['nome']
        paciente.apelido = request.form.get('apelido')
        paciente.nascimento = request.form['nascimento']
        paciente.sexo = request.form['sexo']
        paciente.email = request.form.get('email')
        paciente.celular = request.form.get('celular')
        paciente.rg = request.form.get('rg')
        paciente.cpf = request.form.get('cpf')
        paciente.estado_civil = request.form.get('estado_civil')
        paciente.escolaridade = request.form.get('escolaridade')
        paciente.observacoes = request.form.get('observacoes')
        db.session.commit()
        flash("Paciente atualizado com sucesso!", "success")
        return redirect(url_for('listar_pacientes'))
    return render_template('editar_paciente.html', paciente=paciente)

@app.route('/profissionais/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_profissional(id):
    profissional = Profissional.query.get_or_404(id)
    if request.method == 'POST':
        profissional.nome = request.form['nome']
        profissional.nascimento = request.form['nascimento']
        profissional.sexo = request.form['sexo']
        profissional.cor = request.form['cor']
        profissional.email = request.form['email']
        profissional.estado_civil = request.form['estado_civil']
        profissional.cro = request.form['cro']
        profissional.usuario = request.form.get('usuario')
        profissional.rg = request.form['rg']
        profissional.cpf = request.form['cpf']
        db.session.commit()
        flash("Profissional atualizado com sucesso!", "success")
        return redirect(url_for('listar_profissionais'))
    return render_template('editar_profissional.html', profissional=profissional)

@app.route('/profissionais/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_profissional(id):
    profissional = Profissional.query.get_or_404(id)
    try:
        db.session.delete(profissional)
        db.session.commit()
        flash("Profissional excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir profissional: {str(e)}", "error")
    return redirect(url_for('listar_profissionais'))

@app.route('/pacientes/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    try:
        db.session.delete(paciente)
        db.session.commit()
        flash("Paciente excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir paciente: {str(e)}", "error")
    return redirect(url_for('listar_pacientes'))

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

@app.route('/agendamentos')
@login_required
def listar_agendamentos():
    """
    Exibe uma lista básica de agendamentos ou redireciona ao calendário.
    """
    # Você pode redirecionar direto para o calendário, se preferir:
    return redirect(url_for('calendario'))

@app.route('/agendamentos/calendario')
@login_required
def exibir_calendario():
    """
    Exibe o calendário interativo com os agendamentos.
    """
    return render_template('calendario.html')

@app.route('/agendamentos/novo', methods=['GET', 'POST'])
@login_required
def novo_agendamento():
    if request.method == 'POST':
        paciente = request.form['paciente']
        profissional = request.form['profissional']
        data_hora_inicio = datetime.strptime(request.form['data_hora_inicio'], '%Y-%m-%dT%H:%M')
        data_hora_fim = datetime.strptime(request.form['data_hora_fim'], '%Y-%m-%dT%H:%M')
        observacoes = request.form['observacoes']

        try:
            novo = Agendamento(
                paciente=paciente,
                profissional=profissional,
                data_hora_inicio=data_hora_inicio,
                data_hora_fim=data_hora_fim,
                observacoes=observacoes
            )
            db.session.add(novo)
            db.session.commit()
            print(f"Novo agendamento criado: {novo}")  # Adicione este log
            flash('Agendamento criado com sucesso!', 'success')
            return redirect(url_for('calendario'))
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar agendamento: {e}")  # Adicione este log
            flash(f'Erro ao criar agendamento: {str(e)}', 'error')

    return render_template('novo_agendamento.html')

@app.route('/agendamentos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_agendamento_form():
    agendamento = Agendamento.query.get_or_404(id)

    if request.method == 'POST':
        agendamento.paciente = request.form['paciente']
        agendamento.profissional = request.form['profissional']
        agendamento.data_hora_inicio = datetime.strptime(request.form['data_hora_inicio'], '%Y-%m-%dT%H:%M')
        agendamento.data_hora_fim = datetime.strptime(request.form['data_hora_fim'], '%Y-%m-%dT%H:%M')
        agendamento.observacoes = request.form['observacoes']

        try:
            db.session.commit()
            flash('Agendamento atualizado com sucesso!', 'success')
            return redirect(url_for('calendario'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar agendamento: {str(e)}', 'error')

    return render_template('editar_agendamento.html', agendamento=agendamento)

@app.route('/agendamentos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_agendamento(id):
    agendamento = Agendamento.query.get_or_404(id)

    try:
        db.session.delete(agendamento)
        db.session.commit()
        flash('Agendamento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir agendamento: {str(e)}', 'error')

    return redirect(url_for('calendario'))

@app.route('/pacientes/<int:paciente_id>/orcamento', methods=['GET', 'POST'])
@login_required
def orcamento(paciente_id):
    """
    Exibe a tela de orçamento de um paciente, preenchendo automaticamente o dente caso venha do odontograma.
    """
    paciente = Paciente.query.get_or_404(paciente_id)
    procedimentos = Procedimento.query.all()
    itens_orcamento = ItemOrcamento.query.filter_by(paciente_id=paciente_id).all()

    # Se um dente foi passado na URL, buscamos o status no odontograma
    dente = request.args.get('dente', None)
    odontograma = None
    if dente:
        odontograma = Odontograma.query.filter_by(paciente_id=paciente_id, dente=dente).first()

    if request.method == 'POST':
        dente = request.form['dente']
        procedimento_id = request.form['procedimento']
        observacoes = request.form.get('observacoes', '')

        procedimento = Procedimento.query.get_or_404(procedimento_id)
        novo_item = ItemOrcamento(
            paciente_id=paciente_id,
            dente=dente,
            procedimento_id=procedimento_id,
            observacoes=observacoes,
            preco=procedimento.preco
        )
        db.session.add(novo_item)
        db.session.commit()
        flash('Item adicionado ao orçamento!', 'success')
        return redirect(url_for('orcamento', paciente_id=paciente_id))

    return render_template(
        'orcamento.html',
        paciente=paciente,
        procedimentos=procedimentos,
        itens_orcamento=itens_orcamento,
        dente_selecionado=dente,
        odontograma=odontograma
    )

@app.route('/odontograma/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_odontograma(id):
    dado = Odontograma.query.get_or_404(id)
    if request.method == 'POST':
        dado.dente = request.form['dente']
        dado.status = request.form['status']
        dado.observacoes = request.form.get('observacoes', '')
        db.session.commit()
        flash('Informação do odontograma atualizada com sucesso!', 'success')
        return redirect(url_for('visualizar_odontograma', paciente_id=dado.paciente_id))
    return render_template('editar_odontograma.html', dado=dado)

@app.route('/orcamentos')
@login_required
def orcamentos():
    """
    Tela inicial para selecionar um paciente antes de abrir o orçamento.
    """
    pacientes = Paciente.query.all()
    return render_template('orcamentos.html', pacientes=pacientes)

@app.route('/orcamento/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_orcamento(id):
    item = ItemOrcamento.query.get_or_404(id)
    procedimentos = Procedimento.query.all()

    if request.method == 'POST':
        item.dente = request.form['dente']
        item.procedimento_id = request.form['procedimento']
        item.observacoes = request.form.get('observacoes', '')
        db.session.commit()
        flash('Item do orçamento atualizado!', 'success')
        return redirect(url_for('orcamento', paciente_id=item.paciente_id))

    return render_template('editar_orcamento.html', item=item, procedimentos=procedimentos)

@app.route('/orcamento/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_orcamento(id):
    item = ItemOrcamento.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído do orçamento.', 'success')
    return redirect(url_for('orcamento', paciente_id=item.paciente_id))


@app.route('/procedimentos')
@login_required
def listar_procedimentos():
    procedimentos = Procedimento.query.all()
    return render_template('procedimentos.html', procedimentos=procedimentos)

@app.route('/procedimentos/novo', methods=['GET', 'POST'])
@login_required
def adicionar_procedimento():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao')
        preco = float(request.form['preco'])

        if Procedimento.query.filter_by(nome=nome).first():
            flash('Já existe um procedimento com esse nome.', 'error')
            return redirect(url_for('adicionar_procedimento'))

        novo_procedimento = Procedimento(nome=nome, descricao=descricao, preco=preco)
        db.session.add(novo_procedimento)
        db.session.commit()
        flash('Procedimento adicionado com sucesso!', 'success')
        return redirect(url_for('listar_procedimentos'))

    return render_template('adicionar_procedimento.html')

@app.route('/procedimentos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_procedimento(id):
    procedimento = Procedimento.query.get_or_404(id)
    if request.method == 'POST':
        procedimento.nome = request.form['nome']
        procedimento.descricao = request.form.get('descricao')
        procedimento.preco = float(request.form['preco'])
        db.session.commit()
        flash('Procedimento atualizado com sucesso!', 'success')
        return redirect(url_for('listar_procedimentos'))

    return render_template('editar_procedimento.html', procedimento=procedimento)

@app.route('/procedimentos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_procedimento(id):
    procedimento = Procedimento.query.get_or_404(id)
    try:
        db.session.delete(procedimento)
        db.session.commit()
        flash('Procedimento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir procedimento: {str(e)}', 'error')

    return redirect(url_for('listar_procedimentos'))

@app.route('/pacientes/<int:paciente_id>/odontograma')
@login_required
def visualizar_odontograma(paciente_id):
    """
    Exibe o odontograma do paciente selecionado.
    """
    paciente = Paciente.query.get_or_404(paciente_id)
    dados = Odontograma.query.filter_by(paciente_id=paciente_id).all()
    return render_template('odontograma.html', paciente=paciente, dados=dados)

if __name__ == "__main__":
    app.run(debug=True)
