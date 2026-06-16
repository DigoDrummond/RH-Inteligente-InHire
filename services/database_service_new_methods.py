"""
Novos métodos para Database Service
Adicionar ao final de database_service.py
"""

# ========================================
# MÉTODOS UPSERT PARA NOVAS ENTIDADES
# ========================================

def upsert_requisicao(self, req_api: RequisicaoAPI, vaga_db_id: int = None) -> tuple[bool, str]:
    """
    Insere ou atualiza requisição no banco

    Returns:
        (is_new, operation) - (True/False, 'created'/'updated'/'skipped')
    """
    try:
        existing = self.session.query(Requisicao).filter_by(inhire_id=req_api.id).first()

        if existing:
            # Verificar se precisa atualizar
            if req_api.updatedAt and existing.updated_at_inhire:
                updated_at_normalized = self._normalize_datetime(req_api.updatedAt)
                if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                    return False, 'skipped'

            # Atualizar
            if vaga_db_id:
                existing.vaga_id = vaga_db_id
            existing.job_inhire_id = req_api.jobId
            existing.client_id = req_api.clientId
            existing.status = req_api.status
            existing.reason = req_api.reason
            existing.position_amount = req_api.positionAmount
            existing.requester_id = req_api.requesterId
            existing.requester_name = req_api.requesterName
            existing.approver_id = req_api.approverId
            existing.approver_name = req_api.approverName
            existing.custom_fields = self._serialize_pydantic_to_dict(req_api.customFields)
            existing.requested_at = self._normalize_datetime(req_api.requestedAt)
            existing.approved_at = self._normalize_datetime(req_api.approvedAt)
            existing.rejected_at = self._normalize_datetime(req_api.rejectedAt)
            existing.updated_at_inhire = self._normalize_datetime(req_api.updatedAt)

            self.session.commit()
            return False, 'updated'

        # Criar novo
        nova_req = Requisicao(
            inhire_id=req_api.id,
            vaga_id=vaga_db_id,
            job_inhire_id=req_api.jobId,
            client_id=req_api.clientId,
            status=req_api.status,
            reason=req_api.reason,
            position_amount=req_api.positionAmount,
            requester_id=req_api.requesterId,
            requester_name=req_api.requesterName,
            approver_id=req_api.approverId,
            approver_name=req_api.approverName,
            custom_fields=self._serialize_pydantic_to_dict(req_api.customFields),
            requested_at=self._normalize_datetime(req_api.requestedAt),
            approved_at=self._normalize_datetime(req_api.approvedAt),
            rejected_at=self._normalize_datetime(req_api.rejectedAt),
            created_at_inhire=self._normalize_datetime(req_api.createdAt),
            updated_at_inhire=self._normalize_datetime(req_api.updatedAt)
        )

        self.session.add(nova_req)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de requisição {req_api.id}: {str(e)}")
        raise


def upsert_scorecard_interview(self, interview_api: ScorecardInterviewAPI) -> tuple[bool, str]:
    """
    Insere ou atualiza template de entrevista/scorecard
    """
    try:
        existing = self.session.query(ScorecardInterview).filter_by(inhire_id=interview_api.id).first()

        if existing:
            if interview_api.updatedAt and existing.updated_at_inhire:
                updated_at_normalized = self._normalize_datetime(interview_api.updatedAt)
                if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                    return False, 'skipped'

            existing.name = interview_api.name
            existing.description = interview_api.description
            existing.type = interview_api.type
            existing.questions = self._serialize_pydantic_to_dict(interview_api.questions)
            existing.skill_categories = self._serialize_pydantic_to_dict(interview_api.skillCategories)
            existing.user_id = interview_api.userId
            existing.user_name = interview_api.userName
            existing.tenant_id = interview_api.tenantId
            existing.updated_at_inhire = self._normalize_datetime(interview_api.updatedAt)

            self.session.commit()
            return False, 'updated'

        novo_interview = ScorecardInterview(
            inhire_id=interview_api.id,
            name=interview_api.name,
            description=interview_api.description,
            type=interview_api.type,
            questions=self._serialize_pydantic_to_dict(interview_api.questions),
            skill_categories=self._serialize_pydantic_to_dict(interview_api.skillCategories),
            user_id=interview_api.userId,
            user_name=interview_api.userName,
            tenant_id=interview_api.tenantId,
            created_at_inhire=self._normalize_datetime(interview_api.createdAt),
            updated_at_inhire=self._normalize_datetime(interview_api.updatedAt)
        )

        self.session.add(novo_interview)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de scorecard interview {interview_api.id}: {str(e)}")
        raise


def upsert_scorecard_job(self, scorecard_api: ScorecardJobAPI, vaga_db_id: int = None) -> tuple[bool, str]:
    """
    Insere ou atualiza scorecard de vaga
    """
    try:
        existing = self.session.query(ScorecardJob).filter_by(inhire_id=scorecard_api.id).first()

        if existing:
            if scorecard_api.updatedAt and existing.updated_at_inhire:
                updated_at_normalized = self._normalize_datetime(scorecard_api.updatedAt)
                if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                    return False, 'skipped'

            if vaga_db_id:
                existing.vaga_id = vaga_db_id
            existing.job_inhire_id = scorecard_api.jobId
            existing.skill_categories = self._serialize_pydantic_to_dict(scorecard_api.skillCategories)
            existing.criteria = self._serialize_pydantic_to_dict(scorecard_api.criteria)
            existing.user_id = scorecard_api.userId
            existing.user_name = scorecard_api.userName
            existing.tenant_id = scorecard_api.tenantId
            existing.updated_at_inhire = self._normalize_datetime(scorecard_api.updatedAt)

            self.session.commit()
            return False, 'updated'

        novo_scorecard = ScorecardJob(
            inhire_id=scorecard_api.id,
            vaga_id=vaga_db_id,
            job_inhire_id=scorecard_api.jobId,
            skill_categories=self._serialize_pydantic_to_dict(scorecard_api.skillCategories),
            criteria=self._serialize_pydantic_to_dict(scorecard_api.criteria),
            user_id=scorecard_api.userId,
            user_name=scorecard_api.userName,
            tenant_id=scorecard_api.tenantId,
            created_at_inhire=self._normalize_datetime(scorecard_api.createdAt),
            updated_at_inhire=self._normalize_datetime(scorecard_api.updatedAt)
        )

        self.session.add(novo_scorecard)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de scorecard job {scorecard_api.id}: {str(e)}")
        raise


def upsert_form_response(self, form_api: FormResponseAPI, candidatura_db_id: int) -> tuple[bool, str]:
    """
    Insere ou atualiza respostas de formulário de candidato
    """
    try:
        existing = self.session.query(FormResponse).filter_by(
            candidatura_id=candidatura_db_id,
            candidatura_inhire_id=form_api.jobTalentId
        ).first()

        if existing:
            # Sempre atualizar form responses (não têm updatedAt)
            existing.talent_inhire_id = form_api.talentId
            existing.job_inhire_id = form_api.jobId
            existing.form_type = form_api.formType
            existing.form_id = form_api.formId
            existing.forms_answers = self._serialize_pydantic_to_dict(form_api.formsAnswers)
            existing.personality_answers = self._serialize_pydantic_to_dict(form_api.personalityAnswers)
            existing.disc_interpretation = self._serialize_pydantic_to_dict(form_api.discInterpretation)
            existing.generic_form_responses = self._serialize_pydantic_to_dict(form_api.genericFormResponses)
            existing.submitted_at = self._normalize_datetime(form_api.submittedAt)

            self.session.commit()
            return False, 'updated'

        novo_form = FormResponse(
            candidatura_id=candidatura_db_id,
            candidatura_inhire_id=form_api.jobTalentId,
            talent_inhire_id=form_api.talentId,
            job_inhire_id=form_api.jobId,
            form_type=form_api.formType,
            form_id=form_api.formId,
            forms_answers=self._serialize_pydantic_to_dict(form_api.formsAnswers),
            personality_answers=self._serialize_pydantic_to_dict(form_api.personalityAnswers),
            disc_interpretation=self._serialize_pydantic_to_dict(form_api.discInterpretation),
            generic_form_responses=self._serialize_pydantic_to_dict(form_api.genericFormResponses),
            submitted_at=self._normalize_datetime(form_api.submittedAt)
        )

        self.session.add(novo_form)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de form response {form_api.jobTalentId}: {str(e)}")
        raise


def upsert_vaga_tag(self, tag_api: VagaTagAPI, vaga_db_id: int) -> tuple[bool, str]:
    """
    Insere ou atualiza tag de vaga
    """
    try:
        existing = self.session.query(VagaTag).filter_by(
            vaga_id=vaga_db_id,
            tag_inhire_id=tag_api.id
        ).first()

        if existing:
            existing.name = tag_api.name
            existing.category = tag_api.category
            existing.color = tag_api.color

            self.session.commit()
            return False, 'updated'

        nova_tag = VagaTag(
            vaga_id=vaga_db_id,
            tag_inhire_id=tag_api.id,
            name=tag_api.name,
            category=tag_api.category,
            color=tag_api.color
        )

        self.session.add(nova_tag)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de vaga tag {tag_api.id}: {str(e)}")
        raise


def upsert_automation(self, auto_api: AutomationAPI) -> tuple[bool, str]:
    """
    Insere ou atualiza automação/workflow
    """
    try:
        existing = self.session.query(Automation).filter_by(inhire_id=auto_api.id).first()

        if existing:
            if auto_api.updatedAt and existing.updated_at_inhire:
                updated_at_normalized = self._normalize_datetime(auto_api.updatedAt)
                if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                    return False, 'skipped'

            existing.name = auto_api.name
            existing.description = auto_api.description
            existing.type = auto_api.type
            existing.trigger = self._serialize_pydantic_to_dict(auto_api.trigger)
            existing.conditions = self._serialize_pydantic_to_dict(auto_api.conditions)
            existing.actions = self._serialize_pydantic_to_dict(auto_api.actions)
            existing.is_active = auto_api.isActive
            existing.tenant_id = auto_api.tenantId
            existing.updated_at_inhire = self._normalize_datetime(auto_api.updatedAt)

            self.session.commit()
            return False, 'updated'

        nova_auto = Automation(
            inhire_id=auto_api.id,
            name=auto_api.name,
            description=auto_api.description,
            type=auto_api.type,
            trigger=self._serialize_pydantic_to_dict(auto_api.trigger),
            conditions=self._serialize_pydantic_to_dict(auto_api.conditions),
            actions=self._serialize_pydantic_to_dict(auto_api.actions),
            is_active=auto_api.isActive,
            tenant_id=auto_api.tenantId,
            created_at_inhire=self._normalize_datetime(auto_api.createdAt),
            updated_at_inhire=self._normalize_datetime(auto_api.updatedAt)
        )

        self.session.add(nova_auto)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de automation {auto_api.id}: {str(e)}")
        raise


def upsert_cliente(self, cliente_api: ClienteAPI) -> tuple[bool, str]:
    """
    Insere ou atualiza cliente
    """
    try:
        existing = self.session.query(Cliente).filter_by(inhire_id=cliente_api.id).first()

        if existing:
            if cliente_api.updatedAt and existing.updated_at_inhire:
                updated_at_normalized = self._normalize_datetime(cliente_api.updatedAt)
                if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                    return False, 'skipped'

            existing.name = cliente_api.name
            existing.email = cliente_api.email
            existing.phone = cliente_api.phone
            existing.address = cliente_api.address
            existing.city = cliente_api.city
            existing.state = cliente_api.state
            existing.country = cliente_api.country
            existing.is_active = cliente_api.isActive
            existing.tenant_id = cliente_api.tenantId
            existing.updated_at_inhire = self._normalize_datetime(cliente_api.updatedAt)

            self.session.commit()
            return False, 'updated'

        novo_cliente = Cliente(
            inhire_id=cliente_api.id,
            name=cliente_api.name,
            email=cliente_api.email,
            phone=cliente_api.phone,
            address=cliente_api.address,
            city=cliente_api.city,
            state=cliente_api.state,
            country=cliente_api.country,
            is_active=cliente_api.isActive,
            tenant_id=cliente_api.tenantId,
            created_at_inhire=self._normalize_datetime(cliente_api.createdAt),
            updated_at_inhire=self._normalize_datetime(cliente_api.updatedAt)
        )

        self.session.add(novo_cliente)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de cliente {cliente_api.id}: {str(e)}")
        raise


def upsert_custom_field(self, field_api: CustomFieldAPI) -> tuple[bool, str]:
    """
    Insere ou atualiza custom field
    """
    try:
        existing = self.session.query(CustomField).filter_by(inhire_id=field_api.id).first()

        if existing:
            if field_api.updatedAt and existing.updated_at_inhire:
                updated_at_normalized = self._normalize_datetime(field_api.updatedAt)
                if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                    return False, 'skipped'

            existing.entity_type = field_api.entityType
            existing.field_name = field_api.fieldName
            existing.field_label = field_api.fieldLabel
            existing.field_type = field_api.fieldType
            existing.field_options = self._serialize_pydantic_to_dict(field_api.fieldOptions)
            existing.validation_rules = self._serialize_pydantic_to_dict(field_api.validationRules)
            existing.is_required = field_api.isRequired
            existing.is_active = field_api.isActive
            existing.display_order = field_api.displayOrder
            existing.tenant_id = field_api.tenantId
            existing.updated_at_inhire = self._normalize_datetime(field_api.updatedAt)

            self.session.commit()
            return False, 'updated'

        novo_field = CustomField(
            inhire_id=field_api.id,
            entity_type=field_api.entityType,
            field_name=field_api.fieldName,
            field_label=field_api.fieldLabel,
            field_type=field_api.fieldType,
            field_options=self._serialize_pydantic_to_dict(field_api.fieldOptions),
            validation_rules=self._serialize_pydantic_to_dict(field_api.validationRules),
            is_required=field_api.isRequired,
            is_active=field_api.isActive,
            display_order=field_api.displayOrder,
            tenant_id=field_api.tenantId,
            created_at_inhire=self._normalize_datetime(field_api.createdAt),
            updated_at_inhire=self._normalize_datetime(field_api.updatedAt)
        )

        self.session.add(novo_field)
        self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao fazer upsert de custom field {field_api.id}: {str(e)}")
        raise
