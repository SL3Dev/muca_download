import os
import shutil
import PyInstaller.__main__

def build_app():
    # 1. Limpar builds anteriores
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # 2. Baixar FFmpeg automaticamente (necessário para conversão)
    if not os.path.exists('ffmpeg'):
        os.makedirs('ffmpeg')
        ffmpeg_url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
        print("Baixando FFmpeg...")
        os.system(f'curl -L {ffmpeg_url} -o ffmpeg.zip')
        os.system('unzip ffmpeg.zip -d ffmpeg_temp')
        shutil.move('ffmpeg_temp/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe', 'ffmpeg')
        shutil.rmtree('ffmpeg_temp')
        os.remove('ffmpeg.zip')

    # 3. Executar PyInstaller
    PyInstaller.__main__.run([
        'build.spec',
        '--noconfirm',
        '--clean',
        '--onefile',
        '--windowed'
    ])

    # 4. Copiar arquivos adicionais para a pasta dist
    shutil.copytree('ffmpeg', 'dist/ffmpeg')
    for file in ['icon.png', 'background.png']:
        if os.path.exists(file):
            shutil.copy(file, 'dist')

    print("\n✅ Build concluído com sucesso!")
    print(f"Executável gerado em: {os.path.abspath('dist')}")

if __name__ == '__main__':
    build_app()