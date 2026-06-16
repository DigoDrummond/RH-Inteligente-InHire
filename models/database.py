"""
Modelos SQLAlchemy para o banco de dados PostgreSQL
Representa todas as tabelas do sistema de sincronização Inhire
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Float,
    ForeignKey, JSON, BigInteger, Enum as SQLEnum, Index, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


# ========================================
# Enums
# ========================================

class SyncTypeEnum(str, enum.Enum):
    """Tipos de sincronização"""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"
    MANUAL = "MANUAL"


class SyncStatusEnum(str, enum.Enum):
    """Status de sincronização"""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PARTIAL = "PARTIAL"


class SyncEntityEnum(str, enum.Enum):
    """Entidades sincronizáveis"""
    VAGA = "VAGA"
    POSICAO = "POSICAO"
    CANDIDATURA = "CANDIDATURA"
    TALENTO = "TALENTO"
    REQUISICAO = "REQUISICAO"
    ALL = "ALL"


class VagaStatusEnum(str, enum.Enum):
    """Status de vaga"""
    OPEN = "open"
    CLOSED = "closed"
    PAUSED = "paused"
    CANCELED = "canceled"
    PENDING = "pending"


class SeniorityEnum(str, enum.Enum):
    """Níveis de senioridade"""
    JUNIOR = "junior"
    MID_LEVEL = "mid-level"
    SENIOR = "senior"
    SPECIALIST = "specialist"
    LEADERSHIP = "leadership"


class CandidaturaStatusEnum(str, enum.Enum):
    """Status de candidatura"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    HIRED = "hired"
    REJECTED = "rejected"
    DECLINED = "declined"


# ========================================
# Tabelas de Controle
# ========================================

class SyncConfiguration(Base):
    """Configurações de sincronização por tenant"""
    __tablename__ = 'sync_configuration'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(100), unique=True, nullable=False, index=True)

    # Controles gerais
    sync_enabled = Column(Boolean, default=True, nullable=False)
    auto_sync_enabled = Column(Boolean, default=True, nullable=False)

    # Frequências de sincronização (em minutos)
    sync_frequency_minutes = Column(Integer, default=60, nullable=False)
    full_sync_frequency_hours = Column(Integer, default=24, nullable=False)

    # Controles por entidade
    sync_vagas_enabled = Column(Boolean, default=True, nullable=False)
    sync_posicoes_enabled = Column(Boolean, default=True, nullable=False)
    sync_candidaturas_enabled = Column(Boolean, default=True, nullable=False)
    sync_talentos_enabled = Column(Boolean, default=True, nullable=False)

    # Performance e retry
    max_retry_attempts = Column(Integer, default=3, nullable=False)
    retry_delay_minutes = Column(Integer, default=15, nullable=False)
    batch_size = Column(Integer, default=50, nullable=False)

    # Notificações
    enable_notifications = Column(Boolean, default=False, nullable=False)
    notification_email = Column(String(255))
    webhook_url = Column(String(500))

    # Controle temporal
    last_full_sync = Column(DateTime)
    last_incremental_sync = Column(DateTime)

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    sync_logs = relationship("SyncLog", back_populates="configuration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SyncConfiguration(tenant_id='{self.tenant_id}', enabled={self.sync_enabled})>"


class SyncLog(Base):
    """Log de auditoria de sincronizações"""
    __tablename__ = 'sync_log'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey('sync_configuration.id', ondelete='CASCADE'), nullable=False)

    # Tipo e status
    sync_type = Column(SQLEnum(SyncTypeEnum), nullable=False)
    sync_entity = Column(SQLEnum(SyncEntityEnum), nullable=False)
    status = Column(SQLEnum(SyncStatusEnum), nullable=False)

    # Timing
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    duration_ms = Column(BigInteger)

    # Estatísticas
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Informações detalhadas
    error_messages = Column(Text)
    sync_details = Column(Text)

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    configuration = relationship("SyncConfiguration", back_populates="sync_logs")

    # Índices
    __table_args__ = (
        Index('idx_sync_log_config_start', 'config_id', 'start_time'),
        Index('idx_sync_log_status', 'status'),
        Index('idx_sync_log_entity', 'sync_entity'),
    )

    def __repr__(self):
        return f"<SyncLog(type={self.sync_type}, entity={self.sync_entity}, status={self.status})>"


# ========================================
# Tabelas de Dados Inhire
# ========================================

class Vaga(Base):
    """Vagas/Jobs da Inhire"""
    __tablename__ = 'vagas'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)

    # Dados principais
    name = Column(String(500), nullable=False)
    description = Column(Text)
    area = Column(String(200))
    status = Column(SQLEnum(VagaStatusEnum))
    seniority = Column(SQLEnum(SeniorityEnum))

    # Configurações
    location_required = Column(Boolean, default=False)
    talent_suggestions = Column(Boolean, default=False)
    salary_max = Column(Float)
    sla = Column(BigInteger)  # em segundos
    sla_days_goal = Column(Integer)

    # Métricas
    active_talents = Column(Integer, default=0)
    open_positions = Column(String(50))

    # Responsáveis
    user_id = Column(String(100))
    user_name = Column(String(255))
    manager_id = Column(String(100))
    recruiter_id = Column(String(100))
    tenant_client_id = Column(String(100))

    # IDs adicionais
    origin_id = Column(String(100))

    # Senioridades aceitas (JSON array)
    accepted_seniority = Column(JSON)

    # IDs de avaliadores (JSON array)
    evaluator_ids = Column(JSON)

    # Campos personalizados (JSON)
    custom_fields = Column(JSON)

    # Specialization (Migration 051)
    specialization = Column(String(50))

    # Metadata adicional (Migration 051) - usando 'vaga_metadata' para evitar conflito com SQLAlchemy
    vaga_metadata = Column('metadata', JSON)

    # Auditoria
    created_at_inhire = Column(DateTime)
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    posicoes = relationship("Posicao", back_populates="vaga", cascade="all, delete-orphan")
    candidaturas = relationship("Candidatura", back_populates="vaga", cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index('idx_vaga_status', 'status'),
        Index('idx_vaga_area', 'area'),
        Index('idx_vaga_updated', 'updated_at_inhire'),
    )

    def __repr__(self):
        return f"<Vaga(inhire_id='{self.inhire_id}', name='{self.name}', status={self.status})>"


class Posicao(Base):
    """Posições dentro de vagas"""
    __tablename__ = 'posicoes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)
    vaga_id = Column(BigInteger, ForeignKey('vagas.id', ondelete='CASCADE'), nullable=False)

    # Dados principais
    requisition_id = Column(String(100))
    reason = Column(Text)
    status = Column(String(50))
    talent_id = Column(String(100))

    # Timing
    time_in_current_stage = Column(BigInteger)  # em milissegundos

    # Datas importantes
    approved_at = Column(DateTime)
    hired_at = Column(DateTime)
    opened_at = Column(DateTime)

    # Responsável
    user_id = Column(String(100))
    user_name = Column(String(255))

    # Auditoria
    created_at_inhire = Column(DateTime)
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    vaga = relationship("Vaga", back_populates="posicoes")

    # Índices
    __table_args__ = (
        Index('idx_posicao_vaga', 'vaga_id'),
        Index('idx_posicao_status', 'status'),
        Index('idx_posicao_talent', 'talent_id'),
    )

    def __repr__(self):
        return f"<Posicao(inhire_id='{self.inhire_id}', vaga_id={self.vaga_id}, status='{self.status}')>"


class PositionTimeline(Base):
    """Histórico de mudanças de status das posições"""
    __tablename__ = 'position_timeline'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, index=True)  # ID do evento na InHire (se houver)

    # Relacionamentos
    posicao_id = Column(BigInteger, ForeignKey('posicoes.id', ondelete='CASCADE'), nullable=False)
    vaga_id = Column(BigInteger, ForeignKey('vagas.id', ondelete='SET NULL'))

    # Informações do Evento
    previous_status = Column(String(50))  # Status anterior
    new_status = Column(String(50), nullable=False)  # Novo status
    changed_at = Column(DateTime, nullable=False)  # Timestamp da mudança

    # Auditoria da Mudança
    changed_by = Column(String(100))  # ID do usuário que fez a mudança
    changed_by_name = Column(String(255))  # Nome do usuário
    reason = Column(Text)  # Motivo da mudança
    notes = Column(Text)  # Observações adicionais

    # Metadados
    event_metadata = Column('metadata', JSON)  # Dados adicionais em formato JSON (coluna 'metadata' mapeada como 'event_metadata')

    # Controle Interno
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Índices
    __table_args__ = (
        Index('idx_position_timeline_posicao', 'posicao_id', 'changed_at'),
        Index('idx_position_timeline_vaga', 'vaga_id', 'changed_at'),
        Index('idx_position_timeline_status', 'new_status', 'changed_at'),
        Index('idx_position_timeline_changed_at', 'changed_at'),
    )

    def __repr__(self):
        return f"<PositionTimeline(posicao_id={self.posicao_id}, {self.previous_status or 'NEW'} → {self.new_status}, {self.changed_at})>"


class Candidatura(Base):
    """Candidaturas (relacionamento entre talentos e vagas)"""
    __tablename__ = 'candidaturas'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)
    vaga_id = Column(BigInteger, ForeignKey('vagas.id', ondelete='CASCADE'), nullable=False)
    talento_id = Column(BigInteger, ForeignKey('talentos.id', ondelete='SET NULL'))

    # Dados principais
    talent_inhire_id = Column(String(100), nullable=False, index=True)
    source = Column(String(100))
    status = Column(SQLEnum(CandidaturaStatusEnum))

    # Stage e Phase (JSON)
    stage_id = Column(String(100))
    stage_name = Column(String(255))
    stage_order = Column(Integer)
    phase_id = Column(String(100))
    phase_name = Column(String(255))
    phase_order = Column(Integer)

    # Timing
    time_in_current_stage = Column(BigInteger)  # em milissegundos

    # Resumo do talento (dados do momento da candidatura)
    talent_name = Column(String(255))
    talent_email = Column(String(255))
    talent_headline = Column(String(500))
    talent_company = Column(String(255))
    talent_location = Column(String(255))

    # Responsável
    user_id = Column(String(100))
    user_name = Column(String(255))

    # Metadata completa (Migration 051)
    stage_metadata = Column(JSON)
    phase_metadata = Column(JSON)

    # Auditoria
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    vaga = relationship("Vaga", back_populates="candidaturas")
    talento = relationship("Talento", back_populates="candidaturas")

    # Índices
    __table_args__ = (
        Index('idx_candidatura_vaga', 'vaga_id'),
        Index('idx_candidatura_talento', 'talento_id'),
        Index('idx_candidatura_talent_inhire', 'talent_inhire_id'),
        Index('idx_candidatura_status', 'status'),
    )

    def __repr__(self):
        return f"<Candidatura(inhire_id='{self.inhire_id}', talent='{self.talent_name}', status={self.status})>"


class Talento(Base):
    """Talentos/Candidatos"""
    __tablename__ = 'talentos'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)

    # Dados principais
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    headline = Column(String(500))
    company = Column(String(255))
    location = Column(String(255))
    picture = Column(String(1000))

    # Redes sociais
    linkedin_username = Column(String(255))

    # Configurações
    contact_method = Column(String(50))
    status = Column(String(50))

    # Responsável
    user_id = Column(String(100))
    user_name = Column(String(255))

    # Currículo
    resume = Column(Text)

    # Diversidade (extraído de attributes para facilitar queries)
    diversity_black = Column(Boolean, default=None, nullable=True)
    diversity_woman = Column(Boolean, default=None, nullable=True)
    diversity_lgbt = Column(Boolean, default=None, nullable=True)
    diversity_disability = Column(Boolean, default=None, nullable=True)
    diversity_trans = Column(Boolean, default=None, nullable=True)

    # Attributes (JSON completo)
    attributes = Column(JSON)

    # Jobs/Preferências (JSON array)
    jobs = Column(JSON)

    # Auditoria
    created_at_inhire = Column(DateTime)
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    candidaturas = relationship("Candidatura", back_populates="talento")
    arquivos = relationship("TalentoArquivo", back_populates="talento", cascade="all, delete-orphan")
    tags = relationship("TalentoTag", back_populates="talento", cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index('idx_talento_email', 'email'),
        Index('idx_talento_name', 'name'),
        Index('idx_talento_updated', 'updated_at_inhire'),
        # Índices parciais para diversidade (apenas valores true para economia de espaço)
        Index('idx_talento_diversity_black', 'diversity_black', postgresql_where=text('diversity_black = true')),
        Index('idx_talento_diversity_woman', 'diversity_woman', postgresql_where=text('diversity_woman = true')),
        Index('idx_talento_diversity_lgbt', 'diversity_lgbt', postgresql_where=text('diversity_lgbt = true')),
        Index('idx_talento_diversity_disability', 'diversity_disability', postgresql_where=text('diversity_disability = true')),
        Index('idx_talento_diversity_trans', 'diversity_trans', postgresql_where=text('diversity_trans = true')),
    )

    def __repr__(self):
        return f"<Talento(inhire_id='{self.inhire_id}', name='{self.name}', email='{self.email}')>"


class TalentoArquivo(Base):
    """Arquivos anexados aos talentos (currículos, documentos)"""
    __tablename__ = 'talento_arquivos'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    talento_id = Column(BigInteger, ForeignKey('talentos.id', ondelete='CASCADE'), nullable=False)

    # Dados do arquivo
    file_inhire_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    file_type = Column(String(100))

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    talento = relationship("Talento", back_populates="arquivos")

    # Índices
    __table_args__ = (
        Index('idx_arquivo_talento', 'talento_id'),
    )

    def __repr__(self):
        return f"<TalentoArquivo(name='{self.name}', type='{self.file_type}')>"


class TalentoTag(Base):
    """Tags/habilidades dos talentos"""
    __tablename__ = 'talento_tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    talento_id = Column(BigInteger, ForeignKey('talentos.id', ondelete='CASCADE'), nullable=False)

    # Dados da tag
    tag_inhire_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    talento = relationship("Talento", back_populates="tags")

    # Índices
    __table_args__ = (
        Index('idx_tag_talento', 'talento_id'),
        Index('idx_tag_name', 'name'),
        Index('idx_tag_category', 'category'),
    )

    def __repr__(self):
        return f"<TalentoTag(name='{self.name}', category='{self.category}')>"


class CandidaturaTimeline(Base):
    """Histórico de transições de stages/phases das candidaturas"""
    __tablename__ = 'candidatura_timeline'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidatura_id = Column(BigInteger, ForeignKey('candidaturas.id', ondelete='CASCADE'), nullable=False)

    # ID da candidatura no formato InHire (jobId*talentId)
    candidatura_inhire_id = Column(String(200), nullable=False, index=True)

    # Stage atual
    stage_id = Column(String(100))
    stage_name = Column(String(255))
    stage_order = Column(Integer)
    stage_type = Column(String(100))
    stage_created_at = Column(DateTime)
    stage_updated_at = Column(DateTime)

    # Phase atual
    phase_id = Column(String(100))
    phase_name = Column(String(255))
    phase_order = Column(Integer)
    phase_type = Column(String(100))
    phase_created_at = Column(DateTime)
    phase_updated_at = Column(DateTime)

    # Talent e User relacionados
    talent_inhire_id = Column(String(100), index=True)
    user_id = Column(String(100))
    user_name = Column(String(255))

    # Timestamp da transição
    transition_at = Column(DateTime, nullable=False, index=True)

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    candidatura = relationship("Candidatura")

    # Índices compostos para queries de timeline
    __table_args__ = (
        Index('idx_timeline_candidatura', 'candidatura_id'),
        Index('idx_timeline_candidatura_inhire', 'candidatura_inhire_id'),
        Index('idx_timeline_talent', 'talent_inhire_id'),
        Index('idx_timeline_transition', 'candidatura_id', 'transition_at'),
        Index('idx_timeline_stage', 'stage_id'),
        Index('idx_timeline_phase', 'phase_id'),
    )

    def __repr__(self):
        return f"<CandidaturaTimeline(candidatura='{self.candidatura_inhire_id}', stage='{self.stage_name}', phase='{self.phase_name}', at='{self.transition_at}')>"


class Requisicao(Base):
    """Requisições de vagas (processo de aprovação)"""
    __tablename__ = 'requisicoes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)
    vaga_id = Column(BigInteger, ForeignKey('vagas.id', ondelete='SET NULL'))

    # IDs relacionados
    job_inhire_id = Column(String(100), index=True)
    client_id = Column(String(100))

    # Dados principais
    name = Column(String(500))
    description = Column(Text)
    status = Column(String(50))  # pending, approved, rejected
    reason = Column(Text)
    position_amount = Column(Integer)

    # Salário
    salary_min = Column(Integer)
    salary_max = Column(Integer)

    # Responsáveis
    user_id = Column(String(100))
    user_name = Column(String(255))
    requester_id = Column(String(100))
    requester_name = Column(String(255))
    approver_id = Column(String(100))
    approver_name = Column(String(255))
    tenant_id = Column(String(100))

    # Dados adicionais (JSON)
    custom_fields = Column(JSON)
    positions = Column(JSON)  # Array de posições
    approval_workflow = Column(JSON)  # Workflow de aprovação
    approvers = Column(JSON)  # Lista de aprovadores

    # Timing
    requested_at = Column(DateTime)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    status_updated_at = Column(DateTime)

    # Auditoria
    created_at_inhire = Column(DateTime)
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    vaga = relationship("Vaga")

    # Índices
    __table_args__ = (
        Index('idx_requisicao_vaga', 'vaga_id'),
        Index('idx_requisicao_job_inhire', 'job_inhire_id'),
        Index('idx_requisicao_status', 'status'),
        Index('idx_requisicao_requester', 'requester_id'),
    )

    def __repr__(self):
        return f"<Requisicao(inhire_id='{self.inhire_id}', job_id='{self.job_inhire_id}', status='{self.status}')>"


class VagaTag(Base):
    """Tags/categorias de vagas"""
    __tablename__ = 'vaga_tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vaga_id = Column(BigInteger, ForeignKey('vagas.id', ondelete='CASCADE'), nullable=False)

    # Dados da tag
    tag_inhire_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    color = Column(String(50))

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamentos
    vaga = relationship("Vaga")

    # Índices
    __table_args__ = (
        Index('idx_vaga_tag_vaga', 'vaga_id'),
        Index('idx_vaga_tag_name', 'name'),
        Index('idx_vaga_tag_category', 'category'),
    )

    def __repr__(self):
        return f"<VagaTag(name='{self.name}', category='{self.category}')>"


class Cliente(Base):
    """Clientes do tenant (se multi-client)"""
    __tablename__ = 'clientes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)

    # Dados principais
    name = Column(String(500), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))

    # Endereço
    address = Column(Text)
    city = Column(String(255))
    state = Column(String(100))
    country = Column(String(100))

    # Status
    is_active = Column(Boolean, default=True)

    # Tenant
    tenant_id = Column(String(100), index=True)

    # Auditoria
    created_at_inhire = Column(DateTime)
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Índices
    __table_args__ = (
        Index('idx_cliente_name', 'name'),
        Index('idx_cliente_active', 'is_active'),
        Index('idx_cliente_tenant', 'tenant_id'),
    )

    def __repr__(self):
        return f"<Cliente(inhire_id='{self.inhire_id}', name='{self.name}')>"


class CustomField(Base):
    """Definições de campos customizados"""
    __tablename__ = 'custom_fields'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, nullable=False, index=True)

    # Dados principais
    entity_type = Column(String(50), nullable=False)  # job, talent, jobTalent
    field_name = Column(String(255), nullable=False)
    field_label = Column(String(500))
    field_type = Column(String(50))  # text, number, date, select, etc

    # Configuração (JSON)
    field_options = Column(JSON)  # Para selects, multip choice, etc
    validation_rules = Column(JSON)

    # Status
    is_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Ordem de exibição
    display_order = Column(Integer)

    # Tenant
    tenant_id = Column(String(100), index=True)

    # Auditoria
    created_at_inhire = Column(DateTime)
    updated_at_inhire = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Índices
    __table_args__ = (
        Index('idx_custom_field_entity', 'entity_type'),
        Index('idx_custom_field_name', 'field_name'),
        Index('idx_custom_field_active', 'is_active'),
        Index('idx_custom_field_tenant', 'tenant_id'),
    )

    def __repr__(self):
        return f"<CustomField(entity='{self.entity_type}', name='{self.field_name}', type='{self.field_type}')>"

