#!/bin/bash

# Script per caricare il progetto su GitHub
# Esegui questo script dalla cartella all_matcha_restock_bot3

echo "🚀 Caricamento progetto su GitHub..."

# Inizializza git se non già fatto
git init

# Aggiungi tutti i file
git add .

# Primo commit
git commit -m "Initial commit - Product Monitor Bot"

# Collega al repository remoto (SOSTITUISCI IL TUO USERNAME)
echo "⚠️  ATTENZIONE: Sostituisci 'TUO_USERNAME' con il tuo username GitHub!"
echo "git remote add origin https://github.com/TUO_USERNAME/all_matcha_restock_bot3.git"

# Carica su GitHub
echo "git branch -M main"
echo "git push -u origin main"

echo "✅ Script preparato! Segui le istruzioni sopra."
