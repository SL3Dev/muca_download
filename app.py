import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from pytubefix import YouTube
from pytubefix.cli import on_progress
from slugify import slugify
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Configuração da interface
tema = 'dark'
ctk.set_appearance_mode(tema)
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("YouTube Downloader - SL3DEV")
app.geometry("800x550")

# Configuração do ícone
def carregar_icone():
    try:
        app.iconbitmap("icon.ico")  # Para Windows
    except:
        try:
            img = Image.open("icon.png") if os.path.exists("icon.png") else None
            if img:
                photo = ImageTk.PhotoImage(img)
                app.wm_iconphoto(True, photo)
        except:
            pass

carregar_icone()

# Caminho padrão e arquivo de histórico
destino = Path.home() / "Videos"
HISTORICO_FILE = "historico.json"

# Função para atualizar opções
def atualizar_opcoes(*args):
    escolha = var.get()
    
    if escolha == "Audio":
        formato_menu.configure(values=["MP3"], state="disabled")
        formato_var.set("MP3")
        resolucao_menu.configure(state="disabled")
    else:
        formato_menu.configure(values=["MP4", "AVI"], state="normal")
        resolucao_menu.configure(state="normal")

# Carregar histórico
def carregar_historico():
    try:
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

# Salvar histórico
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
    except:
        pass

# Mostrar histórico
def mostrar_historico():
    historico = carregar_historico()
    if not historico:
        messagebox.showinfo("Histórico", "Nenhum download realizado ainda.")
        return
    
    janela_historico = ctk.CTkToplevel(app)
    janela_historico.title("Histórico de Downloads")
    janela_historico.geometry("600x400")
    
    frame = ctk.CTkFrame(janela_historico)
    frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    scroll = ctk.CTkScrollableFrame(frame)
    scroll.pack(fill='both', expand=True)
    
    for item in reversed(historico):
        frame_item = ctk.CTkFrame(scroll)
        frame_item.pack(fill='x', pady=5)
        
        icone = "🎵" if item["tipo"] == "Audio" else "🎬"
        label_icone = ctk.CTkLabel(frame_item, text=icone, font=("Arial", 14))
        label_icone.pack(side='left', padx=5)
        
        info = f"{item['titulo']}\n{item['data']} - {item['tipo']}"
        label_info = ctk.CTkLabel(frame_item, text=info, anchor='w')
        label_info.pack(side='left', fill='x', expand=True)
        
        def abrir_arquivo(caminho=item['caminho']):
            if os.path.exists(caminho):
                os.startfile(caminho)
            else:
                messagebox.showerror("Erro", "Arquivo não encontrado!")
        
        btn_abrir = ctk.CTkButton(frame_item, text="Abrir", width=60, command=abrir_arquivo)
        btn_abrir.pack(side='right', padx=5)

# Escolher caminho
def escolher_caminho():
    global destino
    destino = Path(filedialog.askdirectory())
    if not destino:
        destino = Path.home() / "Videos"
    label_caminho.configure(text=f"Salvar em: {destino}")

# Encontrar FFmpeg
def encontrar_ffmpeg():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "ffmpeg", "ffmpeg.exe")
    return os.path.join(os.path.dirname(__file__), "ffmpeg", "ffmpeg.exe")

# Download
def iniciar_download():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Erro", "Por favor, insira uma URL!")
        return
    
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        escolha = var.get()
        formato = formato_var.get()
        resolucao = resolucao_var.get()
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if escolha == "Audio":
            audio_stream = yt.streams.filter(only_audio=True).first()
            output_path = destino / f"{slugify(yt.title)}.mp3"
            audio_stream.download(output_path=destino, filename=output_path.name)
            salvar_no_historico(yt.title, url, data_atual, "Audio", output_path)
        else:
            video_streams = yt.streams.filter(file_extension='mp4' if formato == "MP4" else 'avi')
            if resolucao:
                video_stream = video_streams.filter(res=resolucao).first()
            else:
                video_stream = video_streams.get_highest_resolution()
            audio_stream = yt.streams.get_audio_only()
            video_path = destino / f"{yt.video_id}_video.{formato.lower()}"
            audio_path = destino / f"{yt.video_id}_audio.{formato.lower()}"
            output_path = destino / f"{slugify(yt.title)}.{formato.lower()}"
            video_stream.download(output_path=destino, filename=video_path.name)
            audio_stream.download(output_path=destino, filename=audio_path.name)
            ffmpeg_exe = encontrar_ffmpeg()
            comando = [ffmpeg_exe, "-y", "-i", str(video_path), "-i", str(audio_path), "-c:v", "copy", "-c:a", "aac", str(output_path)]
            subprocess.run(comando)
            os.remove(video_path)
            os.remove(audio_path)
            salvar_no_historico(yt.title, url, data_atual, "Vídeo", output_path)
        
        label_resultado.configure(text=f"Download concluído: {yt.title}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro:\n{str(e)}")

# Interface
frame_principal = ctk.CTkFrame(app)
frame_principal.pack(padx=20, pady=20, fill='both', expand=True)

# Frame de entrada
frame_entrada = ctk.CTkFrame(frame_principal)
frame_entrada.pack(fill='x', pady=5)

url_entry = ctk.CTkEntry(frame_entrada, placeholder_text="Digite a URL do vídeo", width=400)
url_entry.pack(side='left', padx=5, expand=True)

# Frame de opções
frame_opcoes = ctk.CTkFrame(frame_principal)
frame_opcoes.pack(fill='x', pady=5)

var = ctk.StringVar(value="Video")
var.trace_add("write", atualizar_opcoes)

radio_video = ctk.CTkRadioButton(frame_opcoes, text="Vídeo + Áudio", variable=var, value="Video")
radio_audio = ctk.CTkRadioButton(frame_opcoes, text="Apenas Áudio", variable=var, value="Audio")
radio_video.pack(side='left', padx=10)
radio_audio.pack(side='left', padx=10)

formato_var = ctk.StringVar(value="MP4")
formato_menu = ctk.CTkOptionMenu(frame_opcoes, variable=formato_var, values=["MP4", "AVI"])
formato_menu.pack(side='left', padx=10)

resolucao_var = ctk.StringVar(value="")
resolucao_menu = ctk.CTkOptionMenu(frame_opcoes, variable=resolucao_var, values=["", "144p", "360p", "720p", "1080p"])
resolucao_menu.pack(side='left', padx=10)

# Frame de ações
frame_acoes = ctk.CTkFrame(frame_principal)
frame_acoes.pack(fill='x', pady=5)

botao_caminho = ctk.CTkButton(frame_acoes, text="📁 Escolher Pasta", command=escolher_caminho)
botao_caminho.pack(side='left', padx=5)

botao_historico = ctk.CTkButton(frame_acoes, text="🕒 Histórico", command=mostrar_historico)
botao_historico.pack(side='left', padx=5)

botao_download = ctk.CTkButton(frame_acoes, text="⬇️ Baixar", command=iniciar_download)
botao_download.pack(side='right', padx=5)

label_caminho = ctk.CTkLabel(frame_principal, text=f"Salvar em: {destino}")
label_caminho.pack(pady=5)

label_resultado = ctk.CTkLabel(frame_principal, text="")
label_resultado.pack(pady=5)

# Rodapé
rodape = ctk.CTkLabel(app, text="autor: SL3DEV", text_color="gray", font=("Arial", 8))
rodape.place(relx=0.01, rely=0.95, anchor='sw')

# Inicializar opções
atualizar_opcoes()

app.mainloop()