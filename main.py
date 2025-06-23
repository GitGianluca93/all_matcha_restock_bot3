#!/usr/bin/env python3
"""
Bot Telegram per monitoraggio prodotti - all_matcha_restock_bot3
"""

import os
import json
import requests
import time
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
import re

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File per salvare i link
LINKS_FILE = 'monitored_links.json'

class ProductMonitor:
    def __init__(self):
        self.monitored_links = self.load_links()
    
    def load_links(self):
        """Carica i link dal file JSON"""
        if os.path.exists(LINKS_FILE):
            try:
                with open(LINKS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Errore nel caricamento links: {e}")
                return {}
        return {}
    
    def save_links(self):
        """Salva i link nel file JSON"""
        try:
            with open(LINKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.monitored_links, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Errore nel salvataggio links: {e}")
    
    def add_link(self, url, name=None):
        """Aggiunge un nuovo link da monitorare"""
        try:
            # Pulisci l'URL
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Se non specificato un nome, usa il dominio
            if not name:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                name = domain.replace('www.', '')
            
            # Ottieni info iniziali del prodotto
            product_info = self.get_product_info(url)
            
            self.monitored_links[url] = {
                'name': name,
                'url': url,
                'last_check': None,
                'last_status': None,
                'last_price': None,
                'in_stock': None,
                'product_title': product_info.get('title', ''),
                'added_date': datetime.now().isoformat()
            }
            
            self.save_links()
            return True, f"✅ Link aggiunto: {name}\n🔗 {url}"
            
        except Exception as e:
            logger.error(f"Errore nell'aggiunta del link: {e}")
            return False, f"❌ Errore nell'aggiunta del link: {str(e)}"
    
    def remove_link(self, url):
        """Rimuove un link dalla lista"""
        if url in self.monitored_links:
            name = self.monitored_links[url]['name']
            del self.monitored_links[url]
            self.save_links()
            return True, f"✅ Link rimosso: {name}"
        return False, "❌ Link non trovato nella lista"
    
    def remove_all_links(self):
        """Rimuove tutti i link"""
        count = len(self.monitored_links)
        self.monitored_links = {}
        self.save_links()
        return f"✅ Rimossi tutti i {count} link dalla lista"
    
    def get_product_info(self, url):
        """Ottiene informazioni sul prodotto"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Cerca il titolo del prodotto
            title = ''
            title_selectors = [
                'h1', 'title', '.product-title', '.product-name', 
                '.item-title', '#product-title', '.entry-title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = soup.title.string if soup.title else 'Prodotto sconosciuto'
            
            # Cerca il prezzo
            price = self.extract_price(soup)
            
            # Determina se è disponibile
            in_stock = self.check_availability(soup, response.text)
            
            return {
                'title': title[:100],  # Limita la lunghezza
                'price': price,
                'in_stock': in_stock,
                'status_code': response.status_code
            }
            
        except Exception as e:
            logger.error(f"Errore nel controllo prodotto {url}: {e}")
            return {
                'title': 'Errore nel controllo',
                'price': None,
                'in_stock': None,
                'error': str(e)
            }
    
    def extract_price(self, soup):
        """Estrae il prezzo dalla pagina"""
        price_selectors = [
            '.price', '.cost', '.amount', '.valor', '.prezzo',
            '[class*="price"]', '[class*="cost"]', '[id*="price"]',
            '.product-price', '.regular-price', '.sale-price'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Cerca pattern di prezzo (numeri con virgola/punto e simboli valuta)
                price_match = re.search(r'[\€\$\£\¥]\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*[\€\$\£\¥]', price_text)
                if price_match:
                    return price_match.group(0)
        
        return None
    
    def check_availability(self, soup, page_text):
        """Controlla se il prodotto è disponibile"""
        # Parole che indicano non disponibilità
        unavailable_keywords = [
            'esaurito', 'non disponibile', 'out of stock', 'sold out',
            'temporarily unavailable', 'currently unavailable', 'fuori stock',
            'prodotto terminato', 'non in magazzino'
        ]
        
        # Parole che indicano disponibilità
        available_keywords = [
            'disponibile', 'in stock', 'available', 'aggiungi al carrello',
            'add to cart', 'buy now', 'acquista ora', 'in magazzino'
        ]
        
        page_text_lower = page_text.lower()
        
        # Controlla le parole chiave di non disponibilità
        for keyword in unavailable_keywords:
            if keyword in page_text_lower:
                return False
        
        # Controlla le parole chiave di disponibilità
        for keyword in available_keywords:
            if keyword in page_text_lower:
                return True
        
        # Se non trova indicatori chiari, assume disponibile
        return True
    
    def check_all_products(self):
        """Controlla tutti i prodotti monitorati"""
        results = []
        
        for url, data in self.monitored_links.items():
            logger.info(f"Controllo prodotto: {data['name']}")
            
            product_info = self.get_product_info(url)
            
            # Aggiorna i dati
            old_status = data.get('in_stock')
            old_price = data.get('last_price')
            
            data['last_check'] = datetime.now().isoformat()
            data['last_status'] = 'available' if product_info['in_stock'] else 'unavailable'
            data['last_price'] = product_info['price']
            data['in_stock'] = product_info['in_stock']
            
            # Determina se ci sono cambiamenti
            status_changed = old_status is not None and old_status != product_info['in_stock']
            price_changed = old_price is not None and old_price != product_info['price']
            
            result = {
                'name': data['name'],
                'url': url,
                'title': product_info['title'],
                'in_stock': product_info['in_stock'],
                'price': product_info['price'],
                'status_changed': status_changed,
                'price_changed': price_changed,
                'old_price': old_price,
                'error': product_info.get('error')
            }
            
            results.append(result)
            
            # Piccola pausa tra i controlli
            time.sleep(2)
        
        self.save_links()
        return results

# Inizializza il monitor
monitor = ProductMonitor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per il comando /start"""
    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi Link", callback_data='add_link')],
        [InlineKeyboardButton("🗑️ Rimuovi Link", callback_data='remove_link')],
        [InlineKeyboardButton("📋 Lista Link", callback_data='list_links')],
        [InlineKeyboardButton("🔍 Controlla Ora", callback_data='check_now')],
        [InlineKeyboardButton("📎 Aggiungi Multi Link", callback_data='add_multi')],
        [InlineKeyboardButton("🗑️ Rimuovi Tutti", callback_data='remove_all')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = """
🤖 **Bot Monitoraggio Prodotti**

Ciao! Sono il tuo assistente per monitorare la disponibilità dei prodotti.

**Cosa posso fare:**
• ➕ Aggiungere link di prodotti da monitorare
• 🗑️ Rimuovere link specifici
• 📋 Mostrare tutti i link monitorati
• 🔍 Controllare immediatamente tutti i prodotti
• 📎 Aggiungere più link contemporaneamente
• 🗑️ Rimuovere tutti i link in una volta

Usa i pulsanti qui sotto per iniziare!
    """
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per i pulsanti inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add_link':
        await query.edit_message_text(
            "📎 **Aggiungi nuovo link**\n\n"
            "Invia il link del prodotto che vuoi monitorare.\n"
            "Puoi anche aggiungere un nome personalizzato:\n\n"
            "Formato: `link` oppure `link|nome`\n\n"
            "Esempio:\n"
            "`https://example.com/prodotto` oppure\n"
            "`https://example.com/prodotto|Il mio prodotto`",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for'] = 'single_link'
    
    elif query.data == 'remove_link':
        if not monitor.monitored_links:
            await query.edit_message_text("❌ Nessun link da rimuovere!")
            return
        
        keyboard = []
        for url, data in monitor.monitored_links.items():
            keyboard.append([InlineKeyboardButton(
                f"🗑️ {data['name']}", 
                callback_data=f'remove_{hash(url) % 10000}'
            )])
        keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data='back_to_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🗑️ **Rimuovi link**\n\nSeleziona il link da rimuovere:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data.startswith('remove_'):
        # Trova il link da rimuovere
        link_hash = query.data.replace('remove_', '')
        for url in monitor.monitored_links:
            if str(hash(url) % 10000) == link_hash:
                success, message = monitor.remove_link(url)
                await query.edit_message_text(message)
                return
        await query.edit_message_text("❌ Link non trovato!")
    
    elif query.data == 'list_links':
        if not monitor.monitored_links:
            message = "📋 **Lista link monitorati**\n\n❌ Nessun link configurato!"
        else:
            message = "📋 **Lista link monitorati**\n\n"
            for i, (url, data) in enumerate(monitor.monitored_links.items(), 1):
                status_emoji = "✅" if data.get('in_stock') else "❌"
                last_check = data.get('last_check', 'Mai')
                if last_check != 'Mai':
                    last_check = datetime.fromisoformat(last_check).strftime('%d/%m %H:%M')
                
                message += f"{i}. {status_emoji} **{data['name']}**\n"
                message += f"   🔗 {url[:50]}{'...' if len(url) > 50 else ''}\n"
                message += f"   📅 Ultimo controllo: {last_check}\n"
                if data.get('last_price'):
                    message += f"   💰 Prezzo: {data['last_price']}\n"
                message += "\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == 'check_now':
        if not monitor.monitored_links:
            await query.edit_message_text("❌ Nessun link da controllare!")
            return
        
        await query.edit_message_text("🔍 **Controllo in corso...**\n\nSto verificando tutti i prodotti, attendere...")
        
        results = monitor.check_all_products()
        
        message = "🔍 **Risultati controllo**\n\n"
        
        for result in results:
            if result.get('error'):
                message += f"❌ **{result['name']}**\n   Errore: {result['error']}\n\n"
                continue
            
            status_emoji = "✅" if result['in_stock'] else "❌"
            change_emoji = ""
            
            if result['status_changed']:
                if result['in_stock']:
                    change_emoji = " 🔄➡️✅ TORNATO DISPONIBILE!"
                else:
                    change_emoji = " 🔄➡️❌ DIVENTATO NON DISPONIBILE!"
            
            message += f"{status_emoji} **{result['name']}**{change_emoji}\n"
            
            if result['price']:
                price_change = ""
                if result['price_changed'] and result['old_price']:
                    price_change = f" (era {result['old_price']})"
                message += f"   💰 Prezzo: {result['price']}{price_change}\n"
            
            message += f"   🔗 {result['url'][:50]}{'...' if len(result['url']) > 50 else ''}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Indietro", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == 'add_multi':
        await query.edit_message_text(
            "📎 **Aggiungi più link**\n\n"
            "Invia più link separati da una nuova riga.\n"
            "Puoi anche aggiungere nomi personalizzati:\n\n"
            "Formato:\n"
            "`link1|nome1`\n"
            "`link2|nome2`\n"
            "`link3`\n\n"
            "Esempio:\n"
            "`https://sito1.com/prodotto|Prodotto 1`\n"
            "`https://sito2.com/item|Prodotto 2`\n"
            "`https://sito3.com/article`",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for'] = 'multi_links'
    
    elif query.data == 'remove_all':
        keyboard = [
            [InlineKeyboardButton("✅ SÌ, rimuovi tutto", callback_data='confirm_remove_all')],
            [InlineKeyboardButton("❌ No, annulla", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        count = len(monitor.monitored_links)
        await query.edit_message_text(
            f"🗑️ **Conferma rimozione**\n\n"
            f"Sei sicuro di voler rimuovere tutti i {count} link monitorati?\n"
            f"Questa azione non può essere annullata!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == 'confirm_remove_all':
        message = monitor.remove_all_links()
        await query.edit_message_text(message)
    
    elif query.data == 'back_to_menu':
        # Torna al menu principale
        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi Link", callback_data='add_link')],
            [InlineKeyboardButton("🗑️ Rimuovi Link", callback_data='remove_link')],
            [InlineKeyboardButton("📋 Lista Link", callback_data='list_links')],
            [InlineKeyboardButton("🔍 Controlla Ora", callback_data='check_now')],
            [InlineKeyboardButton("📎 Aggiungi Multi Link", callback_data='add_multi')],
            [InlineKeyboardButton("🗑️ Rimuovi Tutti", callback_data='remove_all')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🤖 **Bot Monitoraggio Prodotti**\n\n"
            "Seleziona un'azione:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per i messaggi di testo"""
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for == 'single_link':
        text = update.message.text.strip()
        
        # Controlla se c'è un nome personalizzato
        if '|' in text:
            url, name = text.split('|', 1)
            url = url.strip()
            name = name.strip()
        else:
            url = text
            name = None
        
        success, message = monitor.add_link(url, name)
        await update.message.reply_text(message)
        
        # Reset dello stato
        context.user_data.pop('waiting_for', None)
    
    elif waiting_for == 'multi_links':
        lines = update.message.text.strip().split('\n')
        results = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Controlla se c'è un nome personalizzato
            if '|' in line:
                url, name = line.split('|', 1)
                url = url.strip()
                name = name.strip()
            else:
                url = line
                name = None
            
            success, msg = monitor.add_link(url, name)
            results.append(msg)
        
        if results:
            final_message = "📎 **Risultati aggiunta link:**\n\n" + "\n".join(results)
        else:
            final_message = "❌ Nessun link valido trovato!"
        
        await update.message.reply_text(final_message, parse_mode='Markdown')
        
        # Reset dello stato
        context.user_data.pop('waiting_for', None)
    
    else:
        # Messaggio non riconosciuto
        await update.message.reply_text(
            "❓ Non ho capito. Usa /start per vedere i comandi disponibili."
        )

def main():
    """Funzione principale"""
    # Ottieni il token dalle variabili d'ambiente (GitHub Secrets)
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN non trovato nelle variabili d'ambiente!")
        return
    
    if not chat_id:
        logger.error("TELEGRAM_CHAT_ID non trovato nelle variabili d'ambiente!")
        return
    
    # Crea l'applicazione
    application = Application.builder().token(token).build()
    
    # Aggiungi gli handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Avvia il bot
    logger.info("Bot avviato!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
