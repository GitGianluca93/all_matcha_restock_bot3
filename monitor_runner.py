#!/usr/bin/env python3
"""
Runner per il monitoraggio automatico dei prodotti
Questo script viene eseguito da GitHub Actions
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime

# Importa il monitor dal file principale
sys.path.append('.')
from main import ProductMonitor

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(token, chat_id, message, parse_mode='Markdown'):
    """Invia un messaggio via Telegram"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Errore nell'invio messaggio Telegram: {e}")
        return False

def main():
    """Funzione principale per il controllo automatico"""
    # Ottieni le variabili d'ambiente
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        logger.error("Token Telegram o Chat ID mancanti!")
        return
    
    # Inizializza il monitor
    monitor = ProductMonitor()
    
    if not monitor.monitored_links:
        logger.info("Nessun link da monitorare")
        return
    
    logger.info(f"Controllo {len(monitor.monitored_links)} prodotti...")
    
    # Esegui il controllo
    results = monitor.check_all_products()
    
    # Prepara il messaggio di notifica
    notifications = []
    status_changes = []
    price_changes = []
    
    for result in results:
        if result.get('error'):
            continue
        
        # Controlla cambiamenti di stato
        if result['status_changed']:
            if result['in_stock']:
                status_changes.append(f"✅ **{result['name']}** è tornato DISPONIBILE!")
            else:
                status_changes.append(f"❌ **{result['name']}** è diventato NON DISPONIBILE!")
        
        # Controlla cambiamenti di prezzo
        if result['price_changed'] and result['price'] and result['old_price']:
            price_changes.append(f"💰 **{result['name']}** - Prezzo cambiato: {result['old_price']} → {result['price']}")
    
    # Invia notifiche se ci sono cambiamenti importanti
    if status_changes or price_changes:
        message = "🔔 **Aggiornamenti Prodotti**\n\n"
        
        if status_changes:
            message += "**📦 Cambiamenti di disponibilità:**\n"
            message += "\n".join(status_changes) + "\n\n"
        
        if price_changes:
            message += "**💰 Cambiamenti di prezzo:**\n"
            message += "\n".join(price_changes) + "\n\n"
        
        message += f"🕐 Controllo eseguito: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        send_telegram_message(token, chat_id, message)
        logger.info("Notifiche inviate!")
    else:
        logger.info("Nessun cambiamento rilevato")
    
    # Crea un report di stato
    available_count = sum(1 for r in results if r['in_stock'] and not r.get('error'))
    unavailable_count = sum(1 for r in results if not r['in_stock'] and not r.get('error'))
    error_count = sum(1 for r in results if r.get('error'))
    
    logger.info(f"Risultati: {available_count} disponibili, {unavailable_count} non disponibili, {error_count} errori")

if __name__ == '__main__':
    main()
