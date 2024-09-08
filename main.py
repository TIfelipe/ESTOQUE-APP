import os
import platform
import threading
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
import sqlite3
import pandas as pd
from fpdf import FPDF

# Configura o tamanho da janela
Window.size = (400, 400)

# Conectando ao banco de dados SQLite
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()

# Criando a tabela de produtos
cursor.execute(
    '''
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    codigo_barras TEXT NOT NULL,
    quantidade INTEGER NOT NULL
)
'''
)
conn.commit()


class TelaPrincipal(Screen):
    def __init__(self,**kwargs):
        super(TelaPrincipal,self).__init__(**kwargs)
        layout=BoxLayout(orientation='vertical',padding=10,spacing=10)

        # Botões para as ações principais
        botao_adicionar=Button(text='Adicionar Produto',size_hint_y=None,height=50)
        botao_visualizar=Button(text='Visualizar Estoque',size_hint_y=None,height=50)
        botao_buscar=Button(text='Buscar Produto',size_hint_y=None,height=50)
        botao_exportar=Button(text='Exportar Relatório',size_hint_y=None,height=50)
        botao_adicionar.bind(on_release=self.ir_para_tela_adicionar)
        botao_visualizar.bind(on_release=self.ir_para_tela_visualizar)
        botao_buscar.bind(on_release=self.ir_para_tela_buscar)
        botao_exportar.bind(on_release=self.exportar_relatorio)

        layout.add_widget(botao_adicionar)
        layout.add_widget(botao_visualizar)
        layout.add_widget(botao_buscar)
        layout.add_widget(botao_exportar)

        self.add_widget(layout)

    def ir_para_tela_adicionar(self,instance):
        self.manager.current='adicionar'

    def ir_para_tela_visualizar(self,instance):
        self.manager.current='visualizar'

    def ir_para_tela_buscar(self,instance):
        self.manager.current='buscar'

    def exportar_relatorio(self,instance):
        # Exibir popup de carregamento
        self.show_loading_animation()

        # Iniciar a geração do relatório em uma thread separada
        threading.Thread(target=self.gerar_relatorio).start()

    def show_loading_animation(self):
        conteudo=BoxLayout(orientation='vertical',padding=10,spacing=10)
        conteudo.add_widget(Label(text="Gerando relatório..."))

        self.loading_animation=Label(text="•",font_size='40sp')
        conteudo.add_widget(self.loading_animation)

        self.popup_loading=Popup(title='Aguarde',content=conteudo,size_hint=(0.6,0.3))
        self.popup_loading.open()

        # Atualizar a animação periodicamente com intervalo maior
        self.animation_event=Clock.schedule_interval(self.update_animation,0.5)  # Intervalo de 1 segundo

        # Garantir que o popup de carregamento seja fechado após pelo menos 3 segundos
        Clock.schedule_once(self.ensure_loading_time,2)  # Tempo mínimo para a animação

    def update_animation(self,dt):
        if self.loading_animation.text == "•":
            self.loading_animation.text="••"
        elif self.loading_animation.text == "••":
            self.loading_animation.text="•••"
        else:
            self.loading_animation.text="•"

    def ensure_loading_time(self,dt):
        # Garante que a animação de carregamento dure pelo menos 3 segundos
        if hasattr(self,'animation_event'):
            self.animation_event.cancel()

        Clock.schedule_once(self.show_success_message,0)

    def gerar_relatorio(self):
        # Chama as funções de exportação para XLSX e PDF
        self.exportar_para_xlsx()
        self.exportar_para_pdf()
        self.enviar_para_nuvem()

    def enviar_para_nuvem(self):
        # Implemente aqui a função para enviar os dados para a nuvem
        pass

    def acessar_pasta_em_downloads(self):
        try:
            # Detectar o sistema operacional
            if platform.system() == 'Windows':
                # Caminho da pasta local
                pasta=os.path.join(os.path.dirname(__file__),'Estoque')
            else:
                # Caminho de downloads no Android
                pasta = '/storage/emulated/0/Download/Estoque/'

            if not os.path.exists(pasta):
                os.makedirs(pasta)
                mensagem = 'Pasta criada com sucesso'
            else:
                mensagem = 'Pasta já existe'
            return mensagem, pasta
        except Exception as e:
            return f"Erro ao acessar a pasta de downloads: {str(e)}", None

    def exportar_para_xlsx(self):
        # Chamar a função para acessar ou criar a pasta em Downloads
        mensagem, pasta = self.acessar_pasta_em_downloads()
        print(mensagem)

        if pasta:
            caminho_arquivo = os.path.join(pasta, 'relatorio_produtos.xlsx')

            # Cria uma nova conexão dentro da thread
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM produtos")
            produtos = cursor.fetchall()
            df = pd.DataFrame(produtos, columns=['ID', 'Nome', 'Código de Barras', 'Quantidade'])
            df.to_excel(caminho_arquivo, index=False)

            conn.close()

    def exportar_para_pdf(self):
        # Criar uma nova conexão dentro da thread
        conn=sqlite3.connect('inventory.db')
        cursor=conn.cursor()

        cursor.execute("SELECT * FROM produtos")
        produtos=cursor.fetchall()

        # Criar o PDF
        pdf=FPDF()
        pdf.add_page()
        pdf.set_font("Arial",size=12)

        # Título do PDF
        pdf.set_font("Arial",'B',16)
        pdf.cell(200,10,"Relatório de Produtos",ln=True,align='C')
        pdf.ln(10)  # Adicionar espaço abaixo do título

        # Data
        pdf.set_font("Arial",size=12)
        pdf.cell(200,10,f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",ln=True,align='R')
        pdf.ln(10)  # Adicionar espaço abaixo da data

        # Cabeçalho da tabela
        pdf.cell(40,10,'ID',1,0,'C')
        pdf.cell(60,10,'Nome Produto',1,0,'C')
        pdf.cell(60,10,'Código de Barras',1,0,'C')
        pdf.cell(30,10,'Quantidade',1,1,'C')

        # Dados da tabela
        for produto in produtos:
            pdf.cell(40,10,str(produto[0]),1,0,'C')
            pdf.cell(60,10,produto[1],1,0,'C')
            pdf.cell(60,10,produto[2],1,0,'C')
            pdf.cell(30,10,str(produto[3]),1,1,'C')

        # Acessar a pasta correta para salvar o PDF
        mensagem,pasta=self.acessar_pasta_em_downloads()
        if pasta:
            pdf.output(os.path.join(pasta,"relatorio_produtos.pdf"))

        conn.close()

    def show_success_message(self, dt=None):
        if hasattr(self, 'animation_event'):
            self.animation_event.cancel()

        if hasattr(self, 'popup_loading'):
            self.popup_loading.dismiss()

        conteudo = BoxLayout(orientation='vertical', padding=10, spacing=10)
        conteudo.add_widget(Label(text="Arquivos de dados exportados com sucesso!"))
        botao_fechar = Button(text='Fechar')
        botao_fechar.bind(on_release=self.dismiss_popup)
        conteudo.add_widget(botao_fechar)

        self.popup_success = Popup(title='Sucesso', content=conteudo, size_hint=(0.6, 0.3))
        self.popup_success.open()

    def dismiss_popup(self, instance):
        if hasattr(self, 'popup_success'):
            self.popup_success.dismiss()


class TelaVisualizar(Screen):
    def __init__(self, **kwargs):
        super(TelaVisualizar, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Adiciona o botão "Voltar"
        self.botao_voltar=Button(text='Voltar',size_hint_y=None,height=50)
        self.botao_voltar.bind(on_release=self.voltar_para_principal)
        layout.add_widget(self.botao_voltar)

        # ScrollView para listar produtos
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.lista_produtos = BoxLayout(orientation='vertical', size_hint_y=None)
        self.lista_produtos.bind(minimum_height=self.lista_produtos.setter('height'))
        self.scroll_view.add_widget(self.lista_produtos)
        layout.add_widget(self.scroll_view)

        self.add_widget(layout)

    def on_pre_enter(self):
        self.atualizar_lista_produtos()

    def atualizar_lista_produtos(self):
        # Limpa a lista de produtos existente
        self.lista_produtos.clear_widgets()

        # Obtém a lista de produtos do banco de dados
        cursor.execute("SELECT * FROM produtos")
        produtos=cursor.fetchall()

        # Adiciona botões para cada produto
        for produto in produtos:
            btn=Button(text=f"{produto[1]} - {produto[2]} - {produto[3]} unidades",size_hint_y=None,height=40)
            btn.bind(on_release=lambda btn,prod=produto:self.exibir_modal_edicao(prod))
            self.lista_produtos.add_widget(btn)

    def exibir_modal_edicao(self,produto):
        # Cria o layout para o popup
        conteudo=BoxLayout(orientation='vertical',padding=10,spacing=10)

        # Campos de entrada para editar produto
        self.input_nome=TextInput(text=produto[1],hint_text='Nome do Produto',multiline=False)
        self.input_codigo_barras=TextInput(text=produto[2],hint_text='Código de Barras',multiline=False)
        self.input_quantidade=TextInput(text=str(produto[3]),hint_text='Quantidade',input_filter='int',multiline=False)

        conteudo.add_widget(self.input_nome)
        conteudo.add_widget(self.input_codigo_barras)
        conteudo.add_widget(self.input_quantidade)

        # Botões para salvar alterações ou cancelar
        layout_botoes=BoxLayout(size_hint_y=None,height=50)
        botao_salvar=Button(text='Salvar')
        botao_voltar=Button(text='Voltar')

        botao_salvar.bind(on_release=lambda instance:self.salvar_alteracoes(produto[0]))
        botao_voltar.bind(on_release=self.dismiss_popup)

        layout_botoes.add_widget(botao_salvar)
        layout_botoes.add_widget(botao_voltar)
        conteudo.add_widget(layout_botoes)

        # Cria e exibe o popup
        self.popup=Popup(title='Editar Produto',content=conteudo,size_hint=(0.8,0.6))
        self.popup.open()

    def salvar_alteracoes(self,produto_id):
        nome=self.input_nome.text
        codigo_barras=self.input_codigo_barras.text
        quantidade=int(self.input_quantidade.text)

        # Atualiza o produto
        cursor.execute(
            'UPDATE produtos SET nome = ?, codigo_barras = ?, quantidade = ? WHERE id = ?',
            (nome,codigo_barras,quantidade,produto_id)
            )
        conn.commit()
        self.atualizar_lista_produtos()
        self.dismiss_popup()

    def dismiss_popup(self,*args):
        if hasattr(self,'popup'):
            self.popup.dismiss()

    def voltar_para_principal(self,instance):
        self.manager.current='principal'


class TelaAdicionar(Screen):
    def __init__(self, **kwargs):
        super(TelaAdicionar, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Campos de entrada para adicionar produto
        self.input_nome = TextInput(hint_text='Nome do Produto', multiline=False)
        self.input_codigo_barras = TextInput(hint_text='Código de Barras', multiline=False)
        self.input_quantidade = TextInput(hint_text='Quantidade', input_filter='int', multiline=False)

        layout.add_widget(self.input_nome)
        layout.add_widget(self.input_codigo_barras)
        layout.add_widget(self.input_quantidade)

        # Botões para salvar ou cancelar
        layout_botoes = BoxLayout(size_hint_y=None, height=50)
        botao_salvar = Button(text='Salvar')
        botao_cancelar = Button(text='Cancelar')

        botao_salvar.bind(on_release=self.salvar_produto)
        botao_cancelar.bind(on_release=self.ir_para_tela_principal)

        layout_botoes.add_widget(botao_salvar)
        layout_botoes.add_widget(botao_cancelar)
        layout.add_widget(layout_botoes)

        self.add_widget(layout)

    def limpar_inputs(self):
        self.input_nome.text = ''
        self.input_codigo_barras.text = ''
        self.input_quantidade.text = ''

    def salvar_produto(self, instance):
        nome = self.input_nome.text
        codigo_barras = self.input_codigo_barras.text
        quantidade = int(self.input_quantidade.text)

        # Adiciona um novo produto
        cursor.execute(
            'INSERT INTO produtos (nome, codigo_barras, quantidade) VALUES (?, ?, ?)',
            (nome, codigo_barras, quantidade)
        )
        conn.commit()
        App.get_running_app().root.get_screen('visualizar').atualizar_lista_produtos()
        self.ir_para_tela_principal(None)

    def ir_para_tela_principal(self, instance):
        self.manager.current = 'principal'

    def on_pre_enter(self):
        # Limpa o formulário ao entrar na tela
        self.limpar_inputs()


class TelaEditar(Screen):
    def __init__(self, **kwargs):
        super(TelaEditar, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Campos de entrada para editar produto
        self.input_nome = TextInput(hint_text='Nome do Produto', multiline=False)
        self.input_codigo_barras = TextInput(hint_text='Código de Barras', multiline=False)
        self.input_quantidade = TextInput(hint_text='Quantidade', input_filter='int', multiline=False)

        layout.add_widget(self.input_nome)
        layout.add_widget(self.input_codigo_barras)
        layout.add_widget(self.input_quantidade)

        # Botões para salvar alterações ou cancelar
        layout_botoes = BoxLayout(size_hint_y=None, height=50)
        botao_salvar = Button(text='Salvar')
        botao_cancelar = Button(text='Cancelar')

        botao_salvar.bind(on_release=self.salvar_alteracoes)
        botao_cancelar.bind(on_release=self.ir_para_tela_visualizar)

        layout_botoes.add_widget(botao_salvar)
        layout_botoes.add_widget(botao_cancelar)
        layout.add_widget(layout_botoes)

        self.add_widget(layout)

    def set_dados_produto(self, produto):
        self.produto = produto
        self.input_nome.text = produto[1]
        self.input_codigo_barras.text = produto[2]
        self.input_quantidade.text = str(produto[3])

    def salvar_alteracoes(self, instance):
        nome = self.input_nome.text
        codigo_barras = self.input_codigo_barras.text
        quantidade = int(self.input_quantidade.text)

        # Atualiza o produto
        cursor.execute(
            'UPDATE produtos SET nome = ?, codigo_barras = ?, quantidade = ? WHERE id = ?',
            (nome, codigo_barras, quantidade, self.produto[0])
        )
        conn.commit()
        App.get_running_app().root.get_screen('visualizar').atualizar_lista_produtos()
        self.ir_para_tela_visualizar(None)

    def ir_para_tela_visualizar(self, instance):
        self.manager.current = 'visualizar'


class TelaBuscar(Screen):
    def __init__(self, **kwargs):
        super(TelaBuscar, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        busca_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.input_nome = TextInput(hint_text='Nome do Produto', multiline=False, size_hint_x=0.7)
        busca_layout.add_widget(self.input_nome)

        botoes_layout = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=10)
        botao_buscar = Button(text='Buscar', size_hint_x=0.5)
        botao_limpar = Button(text='Limpar', size_hint_x=0.5)
        botao_voltar = Button(text='Voltar', size_hint_x=0.5)

        botao_buscar.bind(on_release=self.buscar_produto)
        botao_limpar.bind(on_release=self.limpar)
        botao_voltar.bind(on_release=self.voltar_para_principal)

        botoes_layout.add_widget(botao_buscar)
        botoes_layout.add_widget(botao_limpar)
        botoes_layout.add_widget(botao_voltar)
        busca_layout.add_widget(botoes_layout)

        layout.add_widget(busca_layout)

        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        self.resultados_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.resultados_container.bind(minimum_height=self.resultados_container.setter('height'))
        self.scroll_view.add_widget(self.resultados_container)
        layout.add_widget(self.scroll_view)

        self.add_widget(layout)

    def voltar_para_principal(self, instance):
        self.limpar()
        self.manager.current = 'principal'

    def buscar_produto(self, *args):
        nome = self.input_nome.text
        if nome != '':
            cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", ('%' + nome + '%',))
            produtos = cursor.fetchall()
            self.atualizar_resultados(produtos)
        else:
            #aviso para preencher o nome de um produto
            self.adicionar_aviso('Por favor, preencha o campo de busca.')

    def limpar(self, *args):
        self.input_nome.text = ''
        self.atualizar_resultados([])

    def adicionar_aviso(self, texto):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=texto)
        layout.add_widget(label)
        self.add_widget(layout)


    def atualizar_resultados(self, produtos):
        self.resultados_container.clear_widgets()

        if produtos:
            for produto in produtos:
                btn = Button(text=f"{produto[1]} - {produto[2]} - {produto[3]} unidades", size_hint_y=None, height=40)
                btn.bind(on_release=lambda btn, prod=produto: self.exibir_modal_opcoes(prod))
                self.resultados_container.add_widget(btn)
        else:
            label_sem_resultados=Label(
                text="Nenhum produto encontrado.",
                size_hint_y=None,
                height=40,  # Ajusta a altura para garantir que o texto tenha espaço
                text_size=(self.width,None),  # Distribui o texto na largura disponível
                halign='center',  # Alinha o texto horizontalmente ao centro
                valign='middle'  # Alinha o texto verticalmente ao centro
                )
            self.resultados_container.add_widget(label_sem_resultados)

    def exibir_modal_opcoes(self, produto):
        conteudo = BoxLayout(orientation='vertical', padding=10, spacing=10)
        conteudo.add_widget(Label(text=f"Selecionado: {produto[1]} - {produto[2]} - {produto[3]} unidades"))

        botoes_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        botao_excluir = Button(text='Excluir')
        botao_editar = Button(text='Editar')
        botao_voltar = Button(text='Voltar')

        botao_excluir.bind(on_release=lambda instance: self.confirmar_exclusao(produto))
        botao_editar.bind(on_release=lambda instance: self.exibir_modal_edicao(produto))
        botao_voltar.bind(on_release=self.dismiss_popup)

        botoes_layout.add_widget(botao_excluir)
        botoes_layout.add_widget(botao_editar)
        botoes_layout.add_widget(botao_voltar)
        conteudo.add_widget(botoes_layout)

        self.popup_opcoes = Popup(title='Opções do Produto', content=conteudo, size_hint=(0.8, 0.6))
        self.popup_opcoes.open()

    def confirmar_exclusao(self, produto):
        conteudo = BoxLayout(orientation='vertical', padding=10, spacing=10)
        conteudo.add_widget(Label(text=f"Tem certeza que deseja excluir o produto '{produto[1]}'?"))

        botoes_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        botao_confirmar = Button(text='Confirmar')
        botao_cancelar = Button(text='Cancelar')

        botao_confirmar.bind(on_release=lambda instance: self.excluir_produto(produto[0]))
        botao_cancelar.bind(on_release=self.dismiss_popup)

        botoes_layout.add_widget(botao_confirmar)
        botoes_layout.add_widget(botao_cancelar)
        conteudo.add_widget(botoes_layout)

        self.popup_confirmacao = Popup(title='Confirmar Exclusão', content=conteudo, size_hint=(0.8, 0.6))
        self.popup_confirmacao.open()

    def excluir_produto(self, produto_id):
        cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
        conn.commit()
        self.dismiss_popup()
        self.mostrar_mensagem_confirmacao()

    def mostrar_mensagem_confirmacao(self):
        conteudo = BoxLayout(orientation='vertical', padding=10, spacing=10)
        conteudo.add_widget(Label(text="Produto excluído com sucesso."))
        botao_fechar = Button(text='Fechar')
        botao_fechar.bind(on_release=self.limpar_resultados_e_fechar_popup)
        conteudo.add_widget(botao_fechar)
        self.popup_confirmacao = Popup(title='Aviso', content=conteudo, size_hint=(0.6, 0.3))
        self.popup_confirmacao.open()

    def limpar_resultados_e_fechar_popup(self, *args):
        self.dismiss_popup()
        self.limpar()

    def exibir_modal_edicao(self, produto):
        conteudo = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.input_nome = TextInput(text=produto[1], hint_text='Nome do Produto', multiline=False)
        self.input_codigo_barras = TextInput(text=produto[2], hint_text='Código de Barras', multiline=False)
        self.input_quantidade = TextInput(text=str(produto[3]), hint_text='Quantidade', input_filter='int', multiline=False)

        conteudo.add_widget(self.input_nome)
        conteudo.add_widget(self.input_codigo_barras)
        conteudo.add_widget(self.input_quantidade)

        layout_botoes = BoxLayout(size_hint_y=None, height=50, spacing=10)
        botao_salvar = Button(text='Salvar')
        botao_voltar = Button(text='Voltar')

        botao_salvar.bind(on_release=lambda instance: self.salvar_alteracoes(produto[0]))
        botao_voltar.bind(on_release=self.dismiss_popup)

        layout_botoes.add_widget(botao_salvar)
        layout_botoes.add_widget(botao_voltar)
        conteudo.add_widget(layout_botoes)

        self.popup_edicao = Popup(title='Editar Produto', content=conteudo, size_hint=(0.8, 0.6))
        self.popup_edicao.open()

    def salvar_alteracoes(self, produto_id):
        nome = self.input_nome.text
        codigo_barras = self.input_codigo_barras.text
        quantidade = int(self.input_quantidade.text)

        cursor.execute(
            'UPDATE produtos SET nome = ?, codigo_barras = ?, quantidade = ? WHERE id = ?',
            (nome, codigo_barras, quantidade, produto_id)
        )
        conn.commit()
        self.dismiss_popup()
        self.buscar_produto()

    def dismiss_popup(self, *args):
        if hasattr(self, 'popup_opcoes'):
            self.popup_opcoes.dismiss()
        if hasattr(self, 'popup_confirmacao'):
            self.popup_confirmacao.dismiss()
        if hasattr(self, 'popup_edicao'):
            self.popup_edicao.dismiss()

    def limpar(self, *args):
        self.input_nome.text = ''
        self.resultados_container.clear_widgets()


class MeuApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(TelaPrincipal(name='principal'))
        sm.add_widget(TelaAdicionar(name='adicionar'))
        sm.add_widget(TelaEditar(name='editar'))
        sm.add_widget(TelaVisualizar(name='visualizar'))
        sm.add_widget(TelaBuscar(name='buscar'))
        return sm



if __name__ == '__main__':
    MeuApp().run()
