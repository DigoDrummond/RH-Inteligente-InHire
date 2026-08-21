"""
Health Check Service - InHire Sync
Endpoint para monitoramento de saúde do sistema

Uso:
    python health_check.py

    Acesso: http://localhost:8080/health
"""
import os
import sys
import psutil
from datetime import datetime, timedelta
from flask import Flask, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Fix encoding
os.environ['PGCLIENTENCODING'] = 'UTF8'

from config import settings
from services.auth_service import AuthService
from models.database import SyncLog

app = Flask(__name__)


class HealthChecker:
    """Realiza verificações de saúde do sistema"""

    def __init__(self):
        self.engine = None
        self.Session = None
        self.auth_service = None

    def _init_db(self):
        """Inicializa conexão com banco"""
        if not self.engine:
            database_url = (
                f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                f"?client_encoding=utf8"
            )
            self.engine = create_engine(database_url, pool_pre_ping=True)
            self.Session = sessionmaker(bind=self.engine)

    def _init_auth(self):
        """Inicializa serviço de autenticação"""
        if not self.auth_service:
            self.auth_service = AuthService()

    def check_database(self):
        """
        Verifica conexão com PostgreSQL

        Returns:
            dict: Status, latência, detalhes
        """
        try:
            self._init_db()
            session = self.Session()

            start = datetime.now()
            session.execute(text('SELECT 1'))
            latency_ms = (datetime.now() - start).total_seconds() * 1000

            # Verificar pool de conexões
            pool = self.engine.pool
            pool_status = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow()
            }

            session.close()

            return {
                'status': 'ok',
                'latency_ms': round(latency_ms, 2),
                'host': f"{settings.DB_HOST}:{settings.DB_PORT}",
                'database': settings.DB_NAME,
                'pool': pool_status
            }

        except OperationalError as e:
            return {
                'status': 'error',
                'message': 'Database connection failed',
                'error': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'Unexpected error',
                'error': str(e)
            }

    def check_inhire_api(self):
        """
        Verifica autenticação com API InHire

        Returns:
            dict: Status, autenticação, detalhes
        """
        try:
            self._init_auth()

            start = datetime.now()
            self.auth_service.ensure_authenticated()
            latency_ms = (datetime.now() - start).total_seconds() * 1000

            return {
                'status': 'ok',
                'authenticated': True,
                'latency_ms': round(latency_ms, 2),
                'base_url': settings.INHIRE_BASE_URL,
                'tenant': settings.INHIRE_TENANT
            }

        except Exception as e:
            return {
                'status': 'error',
                'authenticated': False,
                'message': 'Authentication failed',
                'error': str(e)
            }

    def check_last_sync(self):
        """
        Verifica status da última sincronização

        Returns:
            dict: Status, última sync, idade
        """
        try:
            self._init_db()
            session = self.Session()

            # Buscar última sincronização bem-sucedida
            last_sync = session.query(SyncLog)\
                .filter(SyncLog.status == 'SUCCESS')\
                .order_by(SyncLog.end_time.desc())\
                .first()

            if not last_sync:
                session.close()
                return {
                    'status': 'warning',
                    'message': 'No successful sync found'
                }

            age = datetime.utcnow() - last_sync.end_time
            age_hours = age.total_seconds() / 3600

            # Alertas baseados em idade
            if age_hours < 2:
                status = 'ok'
            elif age_hours < 6:
                status = 'warning'
            else:
                status = 'error'

            session.close()

            return {
                'status': status,
                'last_sync': last_sync.end_time.isoformat(),
                'age_hours': round(age_hours, 2),
                'sync_type': last_sync.sync_type,
                'records_processed': last_sync.records_processed
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': 'Failed to check sync status',
                'error': str(e)
            }

    def check_disk_space(self):
        """
        Verifica espaço em disco

        Returns:
            dict: Status, uso do disco
        """
        try:
            usage = psutil.disk_usage('/')
            used_pct = usage.percent

            # Alertas baseados em uso
            if used_pct < 80:
                status = 'ok'
            elif used_pct < 90:
                status = 'warning'
            else:
                status = 'error'

            return {
                'status': status,
                'disk_usage_pct': used_pct,
                'disk_free_gb': round(usage.free / (1024**3), 2),
                'disk_total_gb': round(usage.total / (1024**3), 2)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': 'Failed to check disk space',
                'error': str(e)
            }

    def check_memory(self):
        """
        Verifica uso de memória

        Returns:
            dict: Status, uso de memória
        """
        try:
            memory = psutil.virtual_memory()
            used_pct = memory.percent

            # Alertas baseados em uso
            if used_pct < 80:
                status = 'ok'
            elif used_pct < 90:
                status = 'warning'
            else:
                status = 'error'

            return {
                'status': status,
                'memory_usage_pct': used_pct,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': 'Failed to check memory',
                'error': str(e)
            }

    def check_cpu(self):
        """
        Verifica uso de CPU

        Returns:
            dict: Status, uso de CPU
        """
        try:
            cpu_pct = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Alertas baseados em uso
            if cpu_pct < 80:
                status = 'ok'
            elif cpu_pct < 95:
                status = 'warning'
            else:
                status = 'error'

            return {
                'status': status,
                'cpu_usage_pct': cpu_pct,
                'cpu_count': cpu_count
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': 'Failed to check CPU',
                'error': str(e)
            }


# Instância global
health_checker = HealthChecker()


@app.route('/health')
def health():
    """
    Endpoint principal de health check

    Returns:
        JSON com status de todas as verificações
        HTTP 200 - Sistema saudável
        HTTP 503 - Sistema degradado ou indisponível
    """
    checks = {
        'database': health_checker.check_database(),
        'inhire_api': health_checker.check_inhire_api(),
        'last_sync': health_checker.check_last_sync(),
        'disk': health_checker.check_disk_space(),
        'memory': health_checker.check_memory(),
        'cpu': health_checker.check_cpu()
    }

    # Verificar se todos os checks críticos estão ok
    critical_checks = ['database', 'inhire_api']
    critical_healthy = all(
        checks[check]['status'] == 'ok'
        for check in critical_checks
    )

    # Verificar se há warnings
    has_warnings = any(
        check['status'] == 'warning'
        for check in checks.values()
    )

    # Determinar status geral
    if critical_healthy and not has_warnings:
        overall_status = 'healthy'
        http_code = 200
    elif critical_healthy:
        overall_status = 'degraded'
        http_code = 200
    else:
        overall_status = 'unhealthy'
        http_code = 503

    response = {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '2.1',
        'checks': checks
    }

    return jsonify(response), http_code


@app.route('/health/live')
def liveness():
    """
    Liveness probe - verifica se aplicação está rodando

    Returns:
        HTTP 200 - Aplicação está viva
        HTTP 503 - Aplicação está travada
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/health/ready')
def readiness():
    """
    Readiness probe - verifica se aplicação está pronta para receber tráfego

    Returns:
        HTTP 200 - Pronta para receber requisições
        HTTP 503 - Não pronta (inicializando ou com problemas)
    """
    # Verificar apenas checks críticos
    checks = {
        'database': health_checker.check_database(),
        'inhire_api': health_checker.check_inhire_api()
    }

    all_ready = all(check['status'] == 'ok' for check in checks.values())

    if all_ready:
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': checks
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': checks
        }), 503


if __name__ == '__main__':
    print("=" * 70)
    print(" Health Check Service - InHire Sync")
    print("=" * 70)
    print()
    print("Endpoints disponíveis:")
    print("  http://localhost:8080/health        - Health check completo")
    print("  http://localhost:8080/health/live   - Liveness probe")
    print("  http://localhost:8080/health/ready  - Readiness probe")
    print()
    print("Iniciando servidor...")
    print()

    app.run(host='0.0.0.0', port=8080, debug=False)
