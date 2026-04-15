import os
import requests
import logging

class HomeAssistantClient:
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = base_url or os.environ.get('HOME_ASSISTANT_URL')
        self.token = token or os.environ.get('HOME_ASSISTANT_TOKEN')
        if self.token and self.base_url:
            self.headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json',
            }
        else:
            self.headers = None
            logging.info('Home Assistant não configurado (HOME_ASSISTANT_URL ou HOME_ASSISTANT_TOKEN vazio)')

    def call_service(self, domain: str, service: str, data: dict):
        if not self.base_url or not self.headers:
            logging.info('HA não configurado — ação simulada: %s.%s %s', domain, service, data)
            return None
        url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            r = requests.post(url, headers=self.headers, json=data, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            logging.exception('Falha ao chamar Home Assistant')
            return None

    def turn_on(self, entity_id: str):
        return self.call_service('light', 'turn_on', {'entity_id': entity_id})

    def turn_off(self, entity_id: str):
        return self.call_service('light', 'turn_off', {'entity_id': entity_id})
