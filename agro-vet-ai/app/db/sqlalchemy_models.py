from sqlalchemy import Column, Integer, Text, ARRAY, DateTime, func, LargeBinary
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class KnowledgeBaseChunk(Base):
    __tablename__ = 'knowledge_base_chunks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    content_type = Column(Text, nullable=True)
    content_name = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    page_number = Column(Integer, nullable=True)
    chunk_number = Column(Integer, nullable=True)
    chapter_title = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    source_document_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<KnowledgeBaseChunk(id={self.id}, page={self.page_number}, chapter='{self.chapter_title}')>"


class Images(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(Integer, nullable=False)
    source_document = Column(Text, nullable=True)
    image_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Images(id={self.id}, chunk_id={self.chunk_id}, source_document='{self.source_document}')>"


class Drug(Base):
    """Модель для таблицы drugs - ветеринарные препараты"""
    __tablename__ = 'drugs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_name = Column(Text, nullable=False)
    generic_name = Column(Text, nullable=False)
    drug_class = Column(Text, nullable=False)
    dosage_form = Column(Text, nullable=False)
    route = Column(Text, nullable=False)
    target_animals = Column(ARRAY(Text), nullable=False)
    manufacturer = Column(Text, nullable=False)
    instruction = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Drug(id={self.id}, trade_name='{self.trade_name}', generic='{self.generic_name}')>"


class DrugChunk(Base):
    """Модель для таблицы drugs_chunks - чанки инструкций препаратов для RAG"""
    __tablename__ = 'drugs_chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Основные поля
    source_file = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    generic_name = Column(Text, nullable=True)

    # Метаданные препарата (денормализованные для быстрого поиска)
    trade_name = Column(Text, nullable=False)
    manufacturer = Column(Text, nullable=True)
    dosage_form = Column(Text, nullable=True)
    route = Column(Text, nullable=True)
    drug_class = Column(Text, nullable=True)
    target_animals = Column(ARRAY(Text), nullable=True)

    # Секция инструкции
    section_type = Column(Text, nullable=False)
    section_title = Column(Text, nullable=True)

    # Вектор для семантического поиска (1536 для text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=True)

    # FTS search vector (автоматически заполняется триггером)
    search_vector = Column(TSVECTOR, nullable=True)

    # Дополнительные метаданные
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DrugChunk(id={self.id}, trade_name='{self.trade_name}', section='{self.section_type}')>"


class SourceDocument(Base):
    __tablename__ = 'source_document'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    language = Column(Text, nullable=True)
    contents = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<SourceDocument(id={self.id}, name='{self.name}', language='{self.language}', contents='{self.contents}')>"