"""
Script para enviar notificação de exportação de candidaturas ao Google Chat
"""
import os
import sys
import json
import requests
from datetime import datetime

def send_webhook_notification():
    """Envia notificação com estatísticas ao Google Chat"""
    try:
        # Webhook URL
        webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAsQjNnCQ/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=wfcKutbf_7S0sG1MUWKB9M6v0p0OBwbCyWygBc_6-30"

        # Lê estatísticas do arquivo JSON
        stats_file = 'logs/export_candidaturas_stats.json'

        if not os.path.exists(stats_file):
            print(f"Arquivo de estatísticas não encontrado: {stats_file}")
            return False

        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)

        # Formata a última sincronização
        ultima_sync = stats.get('ultima_sincronizacao', 'N/A')
        if ultima_sync and ultima_sync != 'N/A':
            # Converte ISO para formato brasileiro
            try:
                dt = datetime.fromisoformat(ultima_sync)
                ultima_sync = dt.strftime('%d/%m/%Y %H:%M:%S')
            except:
                pass

        # Monta mensagem formatada
        message = f"""*📊 CANDIDATURAS - Exportação Concluída*

✅ *Data/Hora:* {stats.get('data_hora_exportacao', 'N/A')}
📝 *Registros:* {stats.get('total_registros', 0):,}
🔄 *Última Sincronização:* {ultima_sync}

_Google Sheets atualizado com sucesso_"""

        # Envia para Google Chat
        payload = {"text": message}
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            print("Notificação enviada com sucesso ao Google Chat")
            return True
        else:
            print(f"Erro ao enviar notificação: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"Erro ao enviar webhook: {str(e)}")
        return False


if __name__ == "__main__":
    success = send_webhook_notification()
    sys.exit(0 if success else 1)
