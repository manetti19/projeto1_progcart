# Importa a biblioteca Streamlit para criar o site.
import streamlit as st
import leafmap.foliumap as leafmap

# Importa o Nominatim, que transforma nomes de lugares em coordenadas.
from geopy.geocoders import Nominatim

# Importa excecoes para tratar possiveis erros na busca.
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Importa a classe responsavel pela busca da imagem Sentinel-2.
from sentinel_searcher import SentinelSearcher


# Cria uma classe para representar o site.
class SiteSentinel:

    # Metodo inicial da classe.
    def __init__(self):

        # Define o titulo da pagina.
        self.titulo = "Busca de Imagens Sentinel-2"

        # Define o texto de instrucao para o usuario.
        self.texto_instrucao = "Digite o nome da cidade"

        # Cria o geocodificador Nominatim.
        self.geolocator = Nominatim(user_agent="site_sentinel")

        # Cria o objeto responsavel pela busca Sentinel-2.
        self.sentinel_searcher = SentinelSearcher()


    # Metodo responsavel por montar a interface do site.
    def criar_interface(self):

        # Mostra o titulo principal do site.
        st.title(self.titulo)

        # Mostra o texto explicativo para o usuario.
        st.write(self.texto_instrucao)

        # Cria a barra de digitacao para o nome da cidade.
        cidade = st.text_input(
            "Cidade",
            placeholder="Exemplo: Rio de Janeiro, Guararapes"
        )

        # Cria o botao de busca.
        botao_buscar = st.button("Buscar")

        # Retorna a cidade digitada e o estado do botao.
        return cidade, botao_buscar


    # Metodo responsavel por transformar o nome da cidade em coordenadas.
    def cidade_para_coordenadas(self, cidade):

        # Tenta executar a busca de coordenadas.
        try:

            # Procura a cidade digitada no servico de geocodificacao.
            localizacao = self.geolocator.geocode(cidade, timeout=10)

            # Verifica se alguma localizacao foi encontrada.
            if localizacao is None:

                # Retorna None caso a cidade nao seja encontrada.
                return None

            # Cria um dicionario com as informacoes encontradas.
            coordenadas = {
                "nome": localizacao.address,
                "latitude": localizacao.latitude,
                "longitude": localizacao.longitude
            }

            # Retorna as coordenadas encontradas.
            return coordenadas

        # Trata erro de tempo limite.
        except GeocoderTimedOut:

            # Mostra uma mensagem de erro no site.
            st.error("A busca demorou muito tempo. Tente novamente.")

            # Retorna None em caso de erro.
            return None

        # Trata erro de indisponibilidade.
        except GeocoderUnavailable:

            # Mostra uma mensagem de erro no site.
            st.error("O servico de geocodificacao esta indisponivel no momento.")

            # Retorna None em caso de erro.
            return None


    # Metodo responsavel por mostrar a cidade encontrada em um mapa.
    def mostrar_mapa_cidade(self, coordenadas):

        # Mostra um subtitulo antes do mapa.
        st.subheader("Mapa da cidade")

        # Cria o mapa centralizado na cidade encontrada.
        mapa = leafmap.Map(
            center=[coordenadas["latitude"], coordenadas["longitude"]],
            zoom=10
        )

        # Adiciona um marcador no ponto encontrado.
        mapa.add_marker(
            location=[coordenadas["latitude"], coordenadas["longitude"]],
            popup=coordenadas["nome"]
        )

        # Exibe o mapa dentro do Streamlit.
        mapa.to_streamlit(height=500)


    # Metodo responsavel por processar a busca completa.
    def buscar_cidade(self, cidade):

        # Mostra uma mensagem indicando que a busca comecou.
        st.write(f"Buscando coordenadas para: {cidade}")

        # Transforma o nome da cidade em coordenadas.
        coordenadas = self.cidade_para_coordenadas(cidade)

        # Verifica se as coordenadas foram encontradas.
        if coordenadas is None:

            # Mostra uma mensagem de aviso.
            st.warning("Nao foi possivel encontrar essa cidade.")

            # Encerra o metodo.
            return

        # Mostra uma mensagem de sucesso.
        st.success("Cidade encontrada!")

        # Mostra o nome completo do local encontrado.
        st.write(f"**Local encontrado:** {coordenadas['nome']}")

        # Mostra a latitude.
        st.write(f"**Latitude:** {coordenadas['latitude']}")

        # Mostra a longitude.
        st.write(f"**Longitude:** {coordenadas['longitude']}")

        # Mostra a cidade encontrada em um mapa.
        self.mostrar_mapa_cidade(coordenadas)

        # Mostra uma mensagem indicando busca da imagem.
        st.write("Buscando imagem Sentinel-2...")

        # Busca a imagem Sentinel-2 usando latitude e longitude.
        resultado = self.sentinel_searcher.buscar_imagem(
            latitude=coordenadas["latitude"],
            longitude=coordenadas["longitude"]
        )

        # Verifica se nenhuma imagem foi encontrada.
        if resultado is None:

            # Mostra aviso caso nao tenha imagem.
            st.warning("Nenhuma imagem Sentinel-2 foi encontrada para essa area.")

            # Encerra o metodo.
            return

        # Mostra mensagem de sucesso.
        st.success("Imagem Sentinel-2 encontrada!")

        # Mostra o bbox usado na busca.
        st.write(f"**BBOX:** {resultado['bbox']}")

        # Mostra a data da imagem.
        st.write(f"**Data da imagem:** {resultado['data']}")

        # Mostra a cobertura de nuvens.
        st.write(f"**Cobertura de nuvens:** {resultado['cobertura_nuvens']}%")

        # Mostra a imagem no site.
        st.image(resultado["image_url"])


    # Metodo principal que executa o site.
    def executar(self):

        # Cria a interface e recebe os valores digitados.
        cidade, botao_buscar = self.criar_interface()

        # Verifica se o botao foi clicado.
        if botao_buscar:

            # Verifica se o usuario digitou alguma cidade.
            if cidade:

                # Executa a busca da cidade e da imagem.
                self.buscar_cidade(cidade)

            # Caso o usuario clique no botao sem digitar cidade.
            else:

                # Mostra uma mensagem de aviso.
                st.warning("Digite o nome de uma cidade antes de buscar.")


# Verifica se este arquivo esta sendo executado diretamente.
if __name__ == "__main__":

    # Cria o objeto do site.
    site = SiteSentinel()

    # Executa o site.
    site.executar()
