"""
Schemas Pydantic para validação de dados da API Inhire
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ========================================
# Schemas de Autenticação
# ========================================

class LoginRequest(BaseModel):
    """Request para login"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response do login"""
    accessToken: str
    refreshToken: str
    expiresIn: Optional[int] = None
    tokenType: Optional[str] = "Bearer"


class RefreshTokenRequest(BaseModel):
    """Request para refresh de token"""
    refreshToken: str


# ========================================
# Schemas de Vagas
# ========================================

class VagaAPI(BaseModel):
    """Schema de vaga retornado pela API"""
    id: str
    name: str
    description: Optional[str] = None
    area: Optional[str] = None
    status: Optional[str] = None
    seniority: Optional[str] = None
    acceptedSeniority: Optional[List[str]] = None
    locationRequired: Optional[bool] = False
    talentSuggestions: Optional[bool] = False
    salaryMax: Optional[float] = None
    sla: Optional[int] = None
    slaDaysGoal: Optional[int] = None
    activeTalents: Optional[int] = 0
    openPositions: Optional[int] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    managerId: Optional[str] = None
    recruiterId: Optional[str] = None
    evaluatorIds: Optional[List[str]] = None
    tenantClientId: Optional[str] = None
    originId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    # Migration 051: Campos opcionais adicionais
    specialization: Optional[str] = None
    duplicateFrom: Optional[Dict[str, Any]] = None
    duplication: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class VagasPaginatedRequest(BaseModel):
    """Request para listar vagas paginadas"""
    exclusiveStartKey: Optional[str] = None
    tenantId: str
    limit: Optional[int] = 50


class VagasPaginatedResponse(BaseModel):
    """Response de vagas paginadas"""
    results: List[VagaAPI]  # API retorna 'results', não 'items'
    startKey: Optional[Dict[str, Any]] = None  # API retorna 'startKey' como objeto cursor
    count: int = 0


# ========================================
# Schemas de Posições
# ========================================

class PosicaoAPI(BaseModel):
    """Schema de posição retornado pela API"""
    id: str
    jobId: str
    requisitionId: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    talentId: Optional[str] = None
    timeInCurrentStage: Optional[int] = None
    approvedAt: Optional[datetime] = None
    hiredAt: Optional[datetime] = None
    openedAt: Optional[datetime] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PosicoesPaginatedRequest(BaseModel):
    """Request para listar posições paginadas"""
    limit: Optional[int] = 50
    startKey: Optional[int] = None


class PosicoesPaginatedResponse(BaseModel):
    """Response de posições paginadas"""
    items: List[PosicaoAPI]
    total: int = 0
    hasMore: bool = False


# ========================================
# Schemas de Candidaturas
# ========================================

class CandidaturaStage(BaseModel):
    """Stage da candidatura"""
    id: str
    name: str
    order: Optional[int] = None

    # Migration 051: Campos opcionais adicionais
    type: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    userId: Optional[str] = None
    userName: Optional[str] = None


class CandidaturaPhase(BaseModel):
    """Phase da candidatura"""
    id: str
    name: str
    order: Optional[int] = None

    # Migration 051: Campos opcionais adicionais
    type: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    userId: Optional[str] = None
    userName: Optional[str] = None


class CandidaturaTalentSummary(BaseModel):
    """Resumo do talento na candidatura"""
    id: str
    name: str
    email: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None


class CandidaturaAPI(BaseModel):
    """Schema de candidatura retornado pela API"""
    id: str
    talentId: str
    source: Optional[str] = None
    stage: Optional[CandidaturaStage] = None
    phase: Optional[CandidaturaPhase] = None
    status: Optional[str] = None
    talent: Optional[CandidaturaTalentSummary] = None
    timeInCurrentStage: Optional[int] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    updatedAt: Optional[datetime] = None
    customFields: Optional[Any] = None  # Migration 069: Custom fields (API retorna List[Dict] OU Dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CandidaturasPaginatedRequest(BaseModel):
    """Request para listar candidaturas paginadas"""
    exclusiveStartKey: Optional[str] = None
    limit: Optional[int] = 50


class CandidaturasPaginatedResponse(BaseModel):
    """Response de candidaturas paginadas"""
    jobTalents: List[CandidaturaAPI]  # API retorna 'jobTalents', não 'items'
    startKey: Optional[Dict[str, Any]] = None  # API retorna 'startKey' como objeto cursor
    count: int = 0


# ========================================
# Schemas de Talentos
# ========================================

class TalentoAttributeValue(BaseModel):
    """Valor de um atributo do talento"""
    value: Any
    source: Optional[str] = None


class TalentoSalary(BaseModel):
    """Salário alvo do talento"""
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = "BRL"


class TalentoJob(BaseModel):
    """Preferências de trabalho do talento"""
    contractType: Optional[List[str]] = None
    locationCity: Optional[str] = None
    locationCountry: Optional[str] = None
    seniority: Optional[str] = None
    area: Optional[str] = None
    customFields: Optional[List[Dict]] = None


class TalentoFile(BaseModel):
    """Arquivo anexado ao talento"""
    id: str
    name: str
    url: Optional[str] = None  # A API do InHire não retorna mais url em todos os arquivos
    type: Optional[str] = None


class TalentoTag(BaseModel):
    """Tag do talento"""
    id: str
    name: str
    category: Optional[str] = None


class TalentoAPI(BaseModel):
    """Schema de talento retornado pela API"""
    id: str
    name: Optional[str] = None  # Opcional pois pode vir vazio em candidaturas
    email: Optional[str] = None
    phone: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    picture: Optional[str] = None
    linkedinUsername: Optional[str] = None
    contactMethod: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    resume: Optional[str] = None
    attributes: Optional[Dict[str, List[TalentoAttributeValue]]] = None
    jobs: Optional[List[TalentoJob]] = None
    files: Optional[List[TalentoFile]] = None
    tags: Optional[List[TalentoTag]] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TalentosPaginatedRequest(BaseModel):
    """Request para listar talentos paginados"""
    exclusiveStartKey: Optional[str] = None
    orderBy: Optional[str] = "updatedAt"
    filter: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 50


class TalentosPaginatedResponse(BaseModel):
    """Response de talentos paginados"""
    items: List[TalentoAPI]  # API retorna 'items' para talentos
    startKey: Optional[Dict[str, Any]] = None  # API retorna 'startKey' como objeto cursor
    count: int = 0


# ========================================
# Schemas de Paginação Genérica
# ========================================

class PaginationRequest(BaseModel):
    """Request genérico de paginação"""
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    exclusiveStartKey: Optional[str] = None


class PaginationResponse(BaseModel):
    """Response genérico de paginação"""
    total: int
    count: int
    hasMore: bool
    lastEvaluatedKey: Optional[str] = None


# ========================================
# Schemas de Erro
# ========================================

class ErrorDetail(BaseModel):
    """Detalhes de erro"""
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Response de erro da API"""
    error: str
    message: str
    statusCode: int
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ========================================
# Schemas de Sincronização
# ========================================

class SyncStats(BaseModel):
    """Estatísticas de sincronização"""
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    duration_ms: Optional[int] = None


class SyncResult(BaseModel):
    """Resultado de sincronização"""
    success: bool
    entity: str
    sync_type: str
    stats: SyncStats
    errors: Optional[List[str]] = None
    start_time: datetime
    end_time: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
