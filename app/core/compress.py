from flask_compress import Compress

compress = Compress()  # Instancia o objeto de compressão para otimizar respostas HTTP

__all__ = ["compress"]  # Exporta a instância de compressão para uso em outros módulos