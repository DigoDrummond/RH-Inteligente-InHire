"""
Schemas Pydantic para novas entidades da API InHire
Data: 25/11/2025
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


# ========================================
# REQUISIÇÕES
# ========================================

class RequisicaoAPI(BaseModel):
    """Schema para requisição de vaga"""
    id: str
    jobId: Optional[str] = None
    clientId: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None

    # Campos retornados pelo endpoint direto /requisitions/{id}
    name: Optional[str] = None
    description: Optional[str] = None
    positions: Optional[List[Dict[str, Any]]] = None
    approvalWorkflow: Optional[Dict[str, Any]] = None
    approvers: Optional[List[Dict[str, Any]]] = None
    salaryMin: Optional[float] = None
    salaryMax: Optional[float] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    tenantId: Optional[str] = None
    statusUpdatedAt: Optional[datetime] = None

    # Campos comuns
    positionAmount: Optional[int] = None
    requesterId: Optional[str] = None
    requesterName: Optional[str] = None
    approverId: Optional[str] = None
    approverName: Optional[str] = None
    customFields: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    requestedAt: Optional[datetime] = None
    approvedAt: Optional[datetime] = None
    rejectedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    @field_validator('customFields', mode='before')
    @classmethod
    def convert_custom_fields(cls, v):
        """Converte customFields de lista para dicionário"""
        if isinstance(v, list):
            # Converter lista de {name, customFieldId, value} para dicionário {name: value}
            result = {}
            for item in v:
                if isinstance(item, dict):
                    name = item.get('name')
                    value = item.get('value', '')
                    if name:
                        result[name] = value
            return result
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "req-123",
                "jobId": "job-456",
                "status": "approved",
                "positionAmount": 2
            }
        }


class RequisicoesPaginatedRequest(BaseModel):
    """Request para listar requisições paginadas"""
    limit: int = Field(default=50, ge=1, le=100)
    exclusiveStartKey: Optional[Dict[str, Any]] = None


class RequisicoesPaginatedResponse(BaseModel):
    """Response para requisições paginadas (NOVO ENDPOINT)"""
    results: List[RequisicaoAPI] = []  # API retorna 'results' ao invés de 'items'
    lastEvaluatedKey: Optional[Union[str, Dict[str, Any]]] = None  # Pode ser string ou dict

    # Alias para compatibilidade - items = results
    @property
    def items(self) -> List[RequisicaoAPI]:
        return self.results

    @field_validator('lastEvaluatedKey', mode='before')
    @classmethod
    def normalize_last_key(cls, v):
        """Normaliza lastEvaluatedKey: converte '0' ou 0 para None"""
        if v in [None, '', '0', 0, {}]:
            return None
        return v


# ========================================
# TAGS
# ========================================

class VagaTagAPI(BaseModel):
    """Schema para tag de vaga"""
    id: str
    name: str
    category: Optional[str] = None
    color: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tag-123",
                "name": "Tecnologia",
                "category": "area"
            }
        }


# ========================================
# CLIENTES
# ========================================

class ClienteAPI(BaseModel):
    """Schema para cliente"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    isActive: bool = True
    tenantId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "client-123",
                "name": "Empresa XYZ",
                "email": "contato@empresa.com"
            }
        }


# ========================================
# JOB DETAILS (Detalhes completos de vaga)
# ========================================

class JobDetailsAPI(BaseModel):
    """Schema para detalhes completos de uma vaga"""
    id: str
    name: str
    description: Optional[str] = None
    area: Optional[str] = None
    status: Optional[str] = None
    seniority: Optional[str] = None
    contractType: Optional[Union[str, List[str]]] = None
    location: Optional[str] = None
    locationRequired: bool = False
    salaryMax: Optional[float] = None
    acceptedSeniority: Optional[List[str]] = None
    activeTalents: int = 0
    openPositions: Optional[int] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    managerId: Optional[str] = None
    recruiterId: Optional[str] = None
    tenantClientId: Optional[str] = None
    evaluatorIds: Optional[List[str]] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    # Campos adicionais que vêm no GET /jobs/:id
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    benefits: Optional[str] = None
    customFields: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None

    @field_validator('contractType', mode='before')
    @classmethod
    def convert_contract_type(cls, v):
        """Converte contractType de lista para string"""
        if isinstance(v, list):
            return v[0] if len(v) > 0 else None
        return v

    @field_validator('customFields', mode='before')
    @classmethod
    def convert_custom_fields(cls, v):
        """Converte customFields de lista para dicionário"""
        if isinstance(v, list):
            # Converter lista de {name, customFieldId, value} para dicionário {name: value}
            return {field.get('name', field.get('customFieldId')): field.get('value') for field in v if isinstance(field, dict)}
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "job-123",
                "name": "Desenvolvedor Python",
                "area": "Tecnologia",
                "status": "open"
            }
        }


# ========================================
# POSITION TIMELINE (Histórico de Posições)
# ========================================

class PositionTimelineEventAPI(BaseModel):
    """Schema para evento do histórico de status de uma posição"""
    id: Optional[str] = None
    positionId: str  # ID da posição
    jobId: str  # ID da vaga
    previousStatus: Optional[str] = None  # Status anterior
    newStatus: str  # Novo status
    changedAt: datetime  # Timestamp da mudança
    changedBy: Optional[str] = None  # ID do usuário que fez a mudança
    changedByName: Optional[str] = None  # Nome do usuário
    reason: Optional[str] = None  # Motivo da mudança
    notes: Optional[str] = None  # Observações adicionais
    eventMetadata: Optional[Dict[str, Any]] = None  # Metadados adicionais (renomeado para evitar conflito com SQLAlchemy)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "timeline-123",
                "positionId": "pos-456",
                "jobId": "job-789",
                "previousStatus": "open",
                "newStatus": "filled",
                "changedAt": "2026-01-20T10:30:00Z",
                "changedBy": "user-123",
                "changedByName": "João Silva"
            }
        }


class PositionTimelinePaginatedResponse(BaseModel):
    """Response para histórico paginado de posições"""
    items: List[PositionTimelineEventAPI]
    lastEvaluatedKey: Optional[Union[str, Dict[str, Any]]] = None
    hasMore: bool = False

    @field_validator('lastEvaluatedKey', mode='before')
    @classmethod
    def normalize_last_key(cls, v):
        """Normaliza lastEvaluatedKey: converte '0' ou 0 para None"""
        if v in [None, '', '0', 0, {}]:
            return None
        return v


# ========================================
# JOB TALENT DETAILS (Detalhes completos de candidatura)
# ========================================

class JobTalentDetailsAPI(BaseModel):
    """Schema para detalhes completos de uma candidatura"""
    id: str  # Format: jobId*talentId
    jobId: str
    talentId: str
    source: Optional[str] = None
    status: Optional[str] = None
    medium: Optional[str] = None
    reason: Optional[str] = None
    feedback: Optional[str] = None

    # Stage e Phase
    stageId: Optional[str] = None
    stageName: Optional[str] = None
    stageOrder: Optional[int] = None
    phaseId: Optional[str] = None
    phaseName: Optional[str] = None
    phaseOrder: Optional[int] = None

    # Timing
    timeInCurrentStage: Optional[int] = None

    # Dados do talento
    talentName: Optional[str] = None
    talentEmail: Optional[str] = None
    talentHeadline: Optional[str] = None
    talentCompany: Optional[str] = None
    talentLocation: Optional[str] = None

    # Responsável
    userId: Optional[str] = None
    userName: Optional[str] = None

    # Timestamps
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "job-123*talent-456",
                "jobId": "job-123",
                "talentId": "talent-456",
                "status": "active"
            }
        }


# ========================================
# CUSTOM FIELDS
# ========================================

class CustomFieldAPI(BaseModel):
    """Schema para definição de custom field"""
    id: Optional[str] = None
    name: Optional[str] = None
    fieldName: Optional[str] = None  # Alguns campos usam fieldName
    fieldType: Optional[str] = None  # text, number, date, select, multiselect, etc
    entityType: Optional[str] = None  # job, talent, jobTalent, requisition
    label: Optional[str] = None
    required: Optional[bool] = False
    options: Optional[Union[List[str], List[Dict[str, Any]]]] = None  # Pode ser lista de strings ou objetos
    defaultValue: Optional[Any] = None
    order: Optional[int] = None
    active: Optional[bool] = True
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    # Campos extras que a API pode retornar
    columnName: Optional[str] = None
    context: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "cf-123",
                "name": "Torre",
                "fieldType": "select",
                "entityType": "job",
                "label": "Torre de Negócio",
                "options": ["Operação", "Tecnologia", "Comercial"]
            }
        }
