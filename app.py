import os
import sys
import json
from pathlib import Path
from datetime import datetime
from pytubefix import YouTube
from pytubefix.cli import on_progress
from slugify import slugify
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import queue
import re
from concurrent.futures import ThreadPoolExecutor

# Função para validar URL
def validar_url(url):
    regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.*"
    return re.match(regex, url) is not None

# Função para atualizar opções de vídeo e áudio
def atualizar_opcoes(*args):
    escolha = var.get()
    if escolha == "Audio":
        formato_menu.configure(values=["MP3"], state="disabled")
        formato_var.set("MP3")
        resolucao_menu.configure(state="disabled")
    else:
        formato_menu.configure(values=["MP4", "AVI"], state="normal")
        resolucao_menu.configure(state="normal")

# Configuração da interface
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Inicializa a aplicação
app = ctk.CTk()
app.title("YouTube Downloader - SL3DEV")
app.geometry("800x550")
app.configure(bg="#2E3A47")

# Caminho padrão e arquivo de histórico
destino = Path.home() / "Videos"
HISTORICO_FILE = "historico.json"

# Funções auxiliares
def carregar_historico():
    try:
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def salvar_no_historico(titulo, url, data, tipo, caminho):
    historico = carregar_historico()
    novo_item = {
        "titulo": titulo,
        "url": url,
        "data": data,
        "tipo": tipo,
        "caminho": str(caminho)
    }
    historico.append(novo_item)
    
    try:
        with open(HISTORICO_FILE, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

def mostrar_historico():
    historico = carregar_historico()
    if not historico:
        messagebox.showinfo("Histórico", "Nenhum download realizado ainda.")
        return
    
    janela_historico = ctk.CTkToplevel(app)
    janela_historico.title("Histórico de Downloads")
    janela_historico.geometry("600x400")
    
    frame = ctk.CTkFrame(janela_historico, fg_color="#3B4A5A")  
    frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    scroll = ctk.CTkScrollableFrame(frame, fg_color="#3B4A5A")  
    scroll.pack(fill='both', expand=True)
    
    for item in reversed(historico):
        frame_item = ctk.CTkFrame(scroll, fg_color="#3B4A5A")  
        frame_item.pack(fill='x', pady=5)
        
        icone = "🎵" if item["tipo"] == "Audio" else "🎬"
        label_icone = ctk.CTkLabel(frame_item, text=icone, font=("Arial", 14), text_color="white")
        label_icone.pack(side='left', padx=5)
        
        info = f"{item['titulo']}\n{item['data']} - {item['tipo']}"
        label_info = ctk.CTkLabel(frame_item, text=info, anchor='w', text_color="white")  
        label_info.pack(side='left', fill='x', expand=True)
        
        def abrir_arquivo(caminho=item['caminho']):
            if os.path.exists(caminho):
                os.startfile(caminho)
            else:
                messagebox.showerror("Erro", "Arquivo não encontrado!")
        
        btn_abrir = ctk.CTkButton(frame_item, text="Abrir", width=60, command=abrir_arquivo, fg_color="#4C6D8C", hover_color="#3A5B77")  
        btn_abrir.pack(side='right', padx=5)

def carregar_tela_carregando(exibir=True):
    global janela_carregando
    if exibir:
        janela_carregando = ctk.CTkToplevel(app)
        janela_carregando.title("Baixando...")
        janela_carregando.geometry("300x100")
        label_carregando = ctk.CTkLabel(janela_carregando, text="Baixando, por favor aguarde...", font=("Arial", 14))
        label_carregando.pack(pady=20)
    else:
        if 'janela_carregando' in globals():
            janela_carregando.destroy()

def escolher_caminho():
    global destino
    destino = Path(filedialog.askdirectory())
    if not destino:
        destino = Path.home() / "Videos"
    label_caminho.configure(text=f"Salvar em: {destino}")

def download_em_thread(yt, url, escolha, formato, resolucao, data_atual, nome_arquivo):
    try:
        if escolha == "Audio":
            # Verificar se existe um stream de áudio
            audio_stream = yt.streams.filter(only_audio=True).first()
            if audio_stream is None:
                raise ValueError("Não foi encontrado um stream de áudio disponível.")
            
            output_path = destino / f"{nome_arquivo}.mp3"
            audio_stream.download(output_path=destino, filename=output_path.name)
            salvar_no_historico(yt.title, url, data_atual, "Audio", output_path)
        else:
            # Filtragem do stream com a resolução solicitada
            video_stream = None
            
            if resolucao != "Selecione a resolução":
                # Encontrar o stream de acordo com a resolução escolhida
                video_stream = yt.streams.filter(file_extension="mp4", res=resolucao).first()
            
            # Se não encontrar o stream específico, pegue o primeiro stream que for progressivo
            if not video_stream:
                video_stream = yt.streams.filter(progressive=True, file_extension="mp4").first()
            
            # Se não encontrar o stream com vídeo e áudio, levanta um erro
            if video_stream is None:
                raise ValueError("Não foi encontrado um stream com vídeo e áudio juntos na resolução especificada.")
            
            # Definir o caminho do arquivo de vídeo
            output_path = destino / f"{nome_arquivo}.mp4"
            
            # Realizar o download
            video_stream.download(output_path=destino, filename=output_path.name)
            salvar_no_historico(yt.title, url, data_atual, "Vídeo", output_path)

        # Verificar se o arquivo foi baixado e exibir
        if os.path.exists(output_path):
            os.startfile(output_path)
        
        # Atualizar a interface com o sucesso do download
        label_resultado.configure(text=f"Download concluído: {yt.title}")
        carregar_tela_carregando(False)
    except Exception as e:
        carregar_tela_carregando(False)
        messagebox.showerror("Erro", f"Ocorreu um erro:\n{str(e)}")

def iniciar_download():
    url = url_entry.get()
    nome_arquivo = nome_arquivo_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira uma URL!")
        return
    
    if not nome_arquivo:
        messagebox.showerror("Erro", "Por favor, insira um nome para o arquivo!")
        return
    
    if not validar_url(url):
        messagebox.showerror("Erro", "Por favor, insira uma URL válida do YouTube!")
        return
    
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        escolha = var.get()
        formato = formato_var.get()
        resolucao = resolucao_var.get()
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        carregar_tela_carregando(True)
        threading.Thread(target=download_em_thread, args=(yt, url, escolha, formato, resolucao, data_atual, nome_arquivo), daemon=True).start()
        
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro:\n{str(e)}")

# Interface gráfica
frame_principal = ctk.CTkFrame(app, fg_color="#2E3A47")
frame_principal.pack(padx=20, pady=20, fill='both', expand=True)

frame_entrada = ctk.CTkFrame(frame_principal, fg_color="#2E3A47")
frame_entrada.pack(fill='x', pady=5)

url_entry = ctk.CTkEntry(frame_entrada, placeholder_text="Digite a URL do vídeo", width=400)
url_entry.pack(side='left', padx=5, expand=True)

nome_arquivo_entry = ctk.CTkEntry(frame_entrada, placeholder_text="Nome do arquivo", width=400)
nome_arquivo_entry.pack(side='left', padx=5, expand=True)

frame_opcoes = ctk.CTkFrame(frame_principal, fg_color="#2E3A47")
frame_opcoes.pack(fill='x', pady=5)

var = ctk.StringVar(value="Video")
var.trace_add("write", atualizar_opcoes)

radio_video = ctk.CTkRadioButton(frame_opcoes, text="Vídeo + Áudio", variable=var, value="Video", text_color="white")
radio_audio = ctk.CTkRadioButton(frame_opcoes, text="Apenas Áudio", variable=var, value="Audio", text_color="white")
radio_video.pack(side='left', padx=10)
radio_audio.pack(side='left', padx=10)

formato_var = ctk.StringVar(value="MP4")
formato_menu = ctk.CTkOptionMenu(frame_opcoes, variable=formato_var, values=["MP4", "AVI"], fg_color="#4C6D8C")
formato_menu.pack(side='left', padx=10)

resolucao_var = ctk.StringVar(value="Selecione a resolução")
resolucao_menu = ctk.CTkOptionMenu(frame_opcoes, variable=resolucao_var, values=["Selecione a resolução", "144p", "360p", "720p", "1080p"], fg_color="#4C6D8C")
resolucao_menu.pack(side='left', padx=10)

frame_acoes = ctk.CTkFrame(frame_principal, fg_color="#2E3A47")
frame_acoes.pack(fill='x', pady=5)

botao_caminho = ctk.CTkButton(frame_acoes, text="📁 Escolher Pasta", command=escolher_caminho, fg_color="#4C6D8C", hover_color="#3A5B77")
botao_caminho.pack(side='left', padx=5)

botao_historico = ctk.CTkButton(frame_acoes, text="🕒 Histórico", command=mostrar_historico, fg_color="#4C6D8C", hover_color="#3A5B77")
botao_historico.pack(side='left', padx=5)

botao_download = ctk.CTkButton(frame_acoes, text="⬇️ Baixar", command=iniciar_download, fg_color="#4C6D8C", hover_color="#3A5B77")
botao_download.pack(side='right', padx=5)

label_caminho = ctk.CTkLabel(frame_principal, text=f"Salvar em: {destino}", text_color="white")
label_caminho.pack(pady=5)

label_resultado = ctk.CTkLabel(frame_principal, text="", text_color="white")
label_resultado.pack(pady=5)

rodape = ctk.CTkLabel(app, text="autor: SL3DEV", text_color="gray", font=("Arial", 8))
rodape.place(relx=0.01, rely=0.95, anchor='sw')

# Inicializar opções
atualizar_opcoes()

app.mainloop()
