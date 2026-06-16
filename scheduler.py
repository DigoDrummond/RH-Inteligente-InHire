# -*- coding: utf-8 -*-
"""
AGENDADOR AUTOMÁTICO - Sincronização InHire
============================================

Executa sincronizações automáticas em intervalos configurados:
- Sync EXPRESS: A cada 15 minutos (~10 min) - Vagas, Posições, Talentos, Scorecards
- Sync COMPLETA: A cada 4 horas (~20 min) - Tudo acima + Candidaturas
- Sync FULL: Domingos 02:00 (~55 min) - Full sync de tudo

USO:
    python scheduler.py

PARAR:
    Ctrl+C
"""
import os
import sys
import signal
from datetime import datetime
import pytz

# Fix de encoding para Windows
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['TZ'] = 'America/Sao_Paulo'

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from services.sync_service import SyncService


class InhireScheduler:
    """Agendador de sincronizações InHire"""

    def __init__(self):
        self.scheduler = BlockingScheduler(timezone='America/Sao_Paulo')
        self.sp_tz = pytz.timezone('America/Sao_Paulo')

        # Setup de database
        self.database_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            f"?client_encoding=utf8"
        )
        self.engine = None
        self.Session = None

        # Registro de handlers
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def _init_database(self):
        """Inicializa conexão com banco de dados"""
        if not self.engine:
            self.engine = create_engine(
                self.database_url,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
                echo=False,
                connect_args={'client_encoding': 'utf8', 'connect_timeout': 10}
            )
            self.Session = sessionmaker(bind=self.engine)

    def _job_listener(self, event):
        """Listener de eventos dos jobs"""
        now = datetime.now(self.sp_tz)

        if event.exception:
            print(f"\n❌ [{now.strftime('%Y-%m-%d %H:%M:%S')}] Job {event.job_id} FALHOU")
            print(f"   Erro: {event.exception}")
        else:
            print(f"\n✅ [{now.strftime('%Y-%m-%d %H:%M:%S')}] Job {event.job_id} executado com sucesso")

    def _run_sync_express(self):
        """Executa sincronização EXPRESS (~10 min) - Vagas, Posições, Talentos, Scorecards"""
        print()
        print("=" * 80)
        print(f" AGENDADOR: Iniciando Sync EXPRESS - {datetime.now(self.sp_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        try:
            self._init_database()
            session = self.Session()

            try:
                sync_service = SyncService(session=session)
                result = sync_service.sync_incremental(express_mode=True)

                stats = result.get('stats', {})
                print(f"\n✅ Sync EXPRESS concluída: {stats.get('processed', 0)} registros processados")
                print(f"   Tempo: ~10 minutos")

            finally:
                session.close()

        except Exception as e:
            print(f"\n❌ Erro na Sync EXPRESS: {str(e)}")
            import traceback
            traceback.print_exc()

    def _run_sync_completa(self):
        """Executa sincronização COMPLETA (~20 min) - Inclui Posições e Candidaturas"""
        print()
        print("=" * 80)
        print(f" AGENDADOR: Iniciando Sync COMPLETA - {datetime.now(self.sp_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        try:
            self._init_database()
            session = self.Session()

            try:
                sync_service = SyncService(session=session)
                result = sync_service.sync_incremental(express_mode=False)

                stats = result.get('stats', {})
                print(f"\n✅ Sync COMPLETA concluída: {stats.get('processed', 0)} registros processados")
                print(f"   Tempo: ~20 minutos")

            finally:
                session.close()

        except Exception as e:
            print(f"\n❌ Erro na Sync COMPLETA: {str(e)}")
            import traceback
            traceback.print_exc()

    def _run_sync_full(self):
        """Executa sincronização FULL (~55 min) - Full sync de tudo"""
        print()
        print("=" * 80)
        print(f" AGENDADOR: Iniciando Sync FULL - {datetime.now(self.sp_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        try:
            self._init_database()
            session = self.Session()

            try:
                sync_service = SyncService(session=session)
                result = sync_service.sync_full()

                stats = result.get('stats', {})
                print(f"\n✅ Sync FULL concluída: {stats.get('processed', 0)} registros processados")
                print(f"   Novos: {stats.get('created', 0)}, Atualizados: {stats.get('updated', 0)}")
                print(f"   Tempo: ~55 minutos")

            finally:
                session.close()

        except Exception as e:
            print(f"\n❌ Erro na Sync FULL: {str(e)}")
            import traceback
            traceback.print_exc()

    def setup_jobs(self):
        """Configura jobs de sincronização"""

        # 1. Sync EXPRESS: A cada 15 minutos (24/7) - INCLUI POSIÇÕES
        self.scheduler.add_job(
            func=self._run_sync_express,
            trigger=CronTrigger(minute='*/15', timezone='America/Sao_Paulo'),
            id='sync_express_15min',
            name='Sync EXPRESS (15 min)',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600  # 10 minutos de tolerância
        )
        print("✅ Job configurado: Sync EXPRESS (a cada 15 min, ~10 min)")

        # 2. Sync COMPLETA: A cada 4 horas (24/7) - INCLUI POSIÇÕES E CANDIDATURAS
        self.scheduler.add_job(
            func=self._run_sync_completa,
            trigger=CronTrigger(hour='*/4', minute=0, timezone='America/Sao_Paulo'),
            id='sync_completa_4h',
            name='Sync COMPLETA (4 horas)',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600  # 10 minutos de tolerância
        )
        print("✅ Job configurado: Sync COMPLETA (a cada 4 horas, ~20 min)")

        # 3. Sync FULL: Domingos às 02:00 - FULL SYNC
        self.scheduler.add_job(
            func=self._run_sync_full,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0, timezone='America/Sao_Paulo'),
            id='sync_full_semanal',
            name='Sync FULL (Domingos 02:00)',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600  # 1 hora de tolerância
        )
        print("✅ Job configurado: Sync FULL (domingos 02:00, ~55 min)")

    def print_schedule(self):
        """Imprime cronograma de execução"""
        print()
        print("=" * 80)
        print(" CRONOGRAMA DE SINCRONIZAÇÕES")
        print("=" * 80)
        print()

        jobs = self.scheduler.get_jobs()

        for job in jobs:
            print(f"Job: {job.name}")
            print(f"  ID: {job.id}")
            print(f"  Trigger: {job.trigger}")
            print(f"  Próxima execução: {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

    def start(self):
        """Inicia agendador"""
        print()
        print("=" * 80)
        print(" AGENDADOR INHIRE - Iniciando")
        print("=" * 80)
        print()
        print(f"Banco de dados: {settings.DB_NAME}")
        print(f"Timezone: America/Sao_Paulo")
        print(f"Início: {datetime.now(self.sp_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        self.setup_jobs()
        self.print_schedule()

        print("=" * 80)
        print(" AGENDADOR ATIVO - Aguardando execuções...")
        print(" Pressione Ctrl+C para parar")
        print("=" * 80)
        print()

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print()
            print()
            print("=" * 80)
            print(" AGENDADOR INHIRE - Encerrando")
            print("=" * 80)
            print()
            self.scheduler.shutdown(wait=False)
            print("✅ Agendador parado com sucesso")


def main():
    """Executa agendador"""
    scheduler = InhireScheduler()

    # Handler para Ctrl+C
    def signal_handler(sig, frame):
        print("\n\n⚠️  Recebido sinal de interrupção, encerrando...")
        scheduler.scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Iniciar
    scheduler.start()


if __name__ == "__main__":
    main()
