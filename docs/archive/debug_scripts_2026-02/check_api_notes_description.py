"""
Investigar se a API retorna descrição dos códigos de 'notes' além do código
"""
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.api_client import InhireAPIClient
from services.auth_service import AuthService

def main():
    auth = AuthService()
    auth.login()

    client = InhireAPIClient()

    # Buscar timeline da posição 1428 (vaga 1183)
    # inhire_id da vaga: 00169fd4-3d24-45d4-a2e0-27cb3667e57d
    vaga_id = "00169fd4-3d24-45d4-a2e0-27cb3667e57d"

    print("=" * 80)
    print(f"Buscando timeline da vaga {vaga_id}")
    print("=" * 80)

    events = list(client.get_position_timeline_by_job(vaga_id))

    print(f"\nTotal de eventos: {len(events)}")

    # Procurar eventos com notes
    events_with_notes = [e for e in events if e.notes]

    print(f"Eventos com notes: {len(events_with_notes)}")

    if events_with_notes:
        print("\n" + "=" * 80)
        print("EVENTOS COM NOTES (mostrando TODOS os campos do objeto)")
        print("=" * 80)

        for i, event in enumerate(events_with_notes, 1):
            print(f"\n--- Evento {i} ---")
            print(f"  newStatus: {event.newStatus}")
            print(f"  notes: {event.notes}")
            print(f"  changedAt: {event.changedAt}")

            # Mostrar TODOS os campos do objeto
            print("\n  TODOS OS CAMPOS DO OBJETO:")
            for field, value in event.__dict__.items():
                if value is not None:
                    print(f"    {field}: {value}")

    # Também verificar o JSON RAW da API
    print("\n" + "=" * 80)
    print("JSON RAW DA API (history com comments)")
    print("=" * 80)

    import requests
    url = f"https://api.inhire.app/jobs/positions/paginated/{vaga_id}"
    headers = {"Authorization": f"Bearer {auth.access_token}"}
    response = requests.post(url, json={"limit": 100, "offset": 0}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        positions = data.get('data', [])

        for pos in positions:
            if 'history' in pos:
                history = pos.get('history', [])
                for h in history:
                    if 'comments' in h and h['comments']:
                        print(f"\nEvento history com comments:")
                        print(json.dumps(h, indent=2, ensure_ascii=False))
                        break

if __name__ == "__main__":
    main()
