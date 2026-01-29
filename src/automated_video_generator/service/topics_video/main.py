from criar_audio import main as criar_audio
from transcricao_audio import main as transcricao_audio
from pegar_camadas import main as pegar_camadas
from pegar_topicos import main as pegar_topicos
from pegar_intervalos import main as pegar_intervalos
from imagens_em_intervalos_topicos import main as imagens_em_intervalos_topicos
from get_frase_imagem_intervalo import main as get_frase_imagem_intervalo
from get_sentido_frase_imagens import main as get_sentido_frase_imagens
from pegar_imagens import main as pegar_imagens
from processamento_de_imagem import main as processamento_de_imagem
from processamento_de_imagem_shorts import main as processamento_de_imagem_shorts
from criar_video_shorts import main as criar_video_shorts
from criar_video_ffmpeg import main as criar_video_ffmpeg
from tryyy import main as tryyy


from cortes_audio import main as cortes_audio

def main(tema):
    #print("CRIANDO AUDIO...")
    criar_audio()

    #print("CRIANDO TRANSCRICAO...")    
    #cortes_audio()
    
    #print("CRIANDO TRANSCRICAO WORDS...")
    #transcricao_audio()
        
    #print("PEGANDO TOPICOS...")
    #pegar_topicos()
    
    #print("PEGANDO INTERVALOS...")
    #pegar_intervalos()
    
    #print("MONTANDO JSON IMAGENS DOS INTERVALOS...")
    #imagens_em_intervalos_topicos()
    
    #print("Adicionando frase a cada imagem dos intervalo...")
    #get_frase_imagem_intervalo()
    
    #print("Adicionando as palavras para busca da imagem...")
    #get_sentido_frase_imagens(tema)
    
        
    #print("PEGANDO IMAGENS DA INTERNET...")
    #pegar_imagens() #criar codigo e entender oque fazer para que venha todas as imagens baixadas da net para evitar que falte alguma e deixe burraco no video
    
    #print("PROCESSANDO IMAGENS...")
    #processamento_de_imagem()

    #print("PROCESSANDO IMAGENS PARA O SHORTS...")
    #processamento_de_imagem_shorts()
    
    #print("CRIANDO VIDEO...")
    #colocar video de fundo intro /
    #SE FOR ANIME TIRAR MUSICA DE FUNDO COLOCAR UMA MAIS DE BOA
    #criar_video_ffmpeg()
    
    #print("CRIANDO VIDEO...")
    #criar_video_shorts()
    
    #tryyy()

if __name__ == "__main__":
    main(" ")
    #INTRO DO VIDEO VOLEY SENSUAL VIDEO