#!/usr/bin/env python3
"""
File Renamer GUI - Interfaccia Grafica
======================================

Interfaccia grafica moderna per il File Renamer CLI Tool.
Rende l'esperienza utente molto più semplice e intuitiva.

Autore: Vincenzo Tesse
Versione: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import subprocess
import re

# Importa la classe FileRenamer dal modulo CLI
try:
    from cli_tool import FileRenamer
except ImportError:
    # Se non riesce a importare, mostra un messaggio di errore
    print("❌ Errore: file_renamer_cli.py non trovato!")
    print("Assicurati che file_renamer_cli.py sia nella stessa directory.")
    sys.exit(1)


class FileRenamerGUI:
    """
    Classe principale per l'interfaccia grafica del File Renamer
    
    Questa classe crea una GUI moderna e intuitiva che permette
    di usare tutte le funzionalità del CLI tool in modo visuale.
    """
    
    def __init__(self, root):
        """
        Inizializza l'interfaccia grafica
        
        Args:
            root: Finestra principale di tkinter
        """
        self.root = root
        self.renamer = None
        self.files_to_process = []
        self.new_names = []
        self.selected_directory = ""
        
        # Configurazione finestra principale
        self.setup_main_window()
        
        # Creazione dell'interfaccia
        self.create_widgets()
        
        # Caricamento configurazioni salvate
        self.load_settings()
    
    def setup_main_window(self):
        """
        Configura la finestra principale con stile moderno
        """
        self.root.title("🔄 Advanced File Renamer - GUI")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Icona personalizzata (se disponibile)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass  # Ignora se l'icona non è disponibile
        
        # Stile moderno
        style = ttk.Style()
        style.theme_use('clam')  # Tema più moderno
        
        # Colori personalizzati
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def create_widgets(self):
        """
        Crea tutti i widget dell'interfaccia
        """
        # Frame principale con scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Titolo
        title_label = ttk.Label(main_frame, text="🔄 Advanced File Renamer", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Notebook per organizzare le sezioni
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Tab 1: Selezione File
        self.create_file_selection_tab(notebook)
        
        # Tab 2: Opzioni di Rinomina
        self.create_rename_options_tab(notebook)
        
        # Tab 3: Anteprima e Esecuzione
        self.create_preview_tab(notebook)
        
        # Tab 4: Log e Statistiche
        self.create_log_tab(notebook)
        
        # Barra di stato
        self.create_status_bar(main_frame)
    
    def create_file_selection_tab(self, notebook):
        """
        Crea il tab per la selezione dei file
        """
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📁 Selezione File")
        
        # Sezione directory
        dir_frame = ttk.LabelFrame(frame, text="Directory di Lavoro", padding=10)
        dir_frame.pack(fill='x', pady=(0, 10))
        
        dir_control_frame = ttk.Frame(dir_frame)
        dir_control_frame.pack(fill='x')
        
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_control_frame, textvariable=self.dir_var, font=('Courier', 10))
        self.dir_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(dir_control_frame, text="Sfoglia", command=self.browse_directory).pack(side='right')
        
        # Sezione pattern e filtri
        filter_frame = ttk.LabelFrame(frame, text="Filtri e Pattern", padding=10)
        filter_frame.pack(fill='x', pady=(0, 10))
        
        # Pattern di ricerca
        pattern_frame = ttk.Frame(filter_frame)
        pattern_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(pattern_frame, text="Pattern:").pack(side='left')
        self.pattern_var = tk.StringVar(value="*")
        pattern_entry = ttk.Entry(pattern_frame, textvariable=self.pattern_var, width=20)
        pattern_entry.pack(side='left', padx=(5, 10))
        
        # Checkbox ricorsivo
        self.recursive_var = tk.BooleanVar()
        ttk.Checkbutton(pattern_frame, text="Ricerca ricorsiva", variable=self.recursive_var).pack(side='left')
        
        # Bottone scansione
        scan_button = ttk.Button(filter_frame, text="🔍 Scansiona File", command=self.scan_files)
        scan_button.pack(pady=(10, 0))
        
        # Lista file trovati
        files_frame = ttk.LabelFrame(frame, text="File Trovati", padding=10)
        files_frame.pack(fill='both', expand=True)
        
        # Treeview per mostrare i file
        columns = ('Nome', 'Dimensione', 'Ultima Modifica')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=10)
        
        # Configurazione colonne
        self.files_tree.heading('Nome', text='Nome File')
        self.files_tree.heading('Dimensione', text='Dimensione')
        self.files_tree.heading('Ultima Modifica', text='Ultima Modifica')
        
        self.files_tree.column('Nome', width=400)
        self.files_tree.column('Dimensione', width=100)
        self.files_tree.column('Ultima Modifica', width=150)
        
        # Scrollbar per la treeview
        scrollbar = ttk.Scrollbar(files_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Label contatore file
        self.files_count_label = ttk.Label(files_frame, text="Nessun file selezionato")
        self.files_count_label.pack(pady=(5, 0))
    
    def create_rename_options_tab(self, notebook):
        """
        Crea il tab per le opzioni di rinomina
        """
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚙️ Opzioni Rinomina")
        
        # Variabile per il tipo di rinomina
        self.rename_type = tk.StringVar(value="sequential")
        
        # Sezione tipo di rinomina
        type_frame = ttk.LabelFrame(frame, text="Tipo di Rinomina", padding=10)
        type_frame.pack(fill='x', pady=(0, 10))
        
        # Opzioni radio
        options_frame = ttk.Frame(type_frame)
        options_frame.pack(fill='x')
        
        ttk.Radiobutton(options_frame, text="Sequenziale", variable=self.rename_type, 
                       value="sequential", command=self.on_rename_type_change).pack(anchor='w')
        ttk.Radiobutton(options_frame, text="Pattern Personalizzato", variable=self.rename_type, 
                       value="pattern", command=self.on_rename_type_change).pack(anchor='w')
        ttk.Radiobutton(options_frame, text="Trasformazione Case", variable=self.rename_type, 
                       value="case", command=self.on_rename_type_change).pack(anchor='w')
        ttk.Radiobutton(options_frame, text="Regex", variable=self.rename_type, 
                       value="regex", command=self.on_rename_type_change).pack(anchor='w')
        
        # Frame per le opzioni specifiche
        self.options_frame = ttk.LabelFrame(frame, text="Configurazione", padding=10)
        self.options_frame.pack(fill='x', pady=(0, 10))
        
        # Inizializza con opzioni sequenziali
        self.create_sequential_options()
        
        # Sezione opzioni avanzate
        advanced_frame = ttk.LabelFrame(frame, text="Opzioni Avanzate", padding=10)
        advanced_frame.pack(fill='x')
        
        # Dry run
        self.dry_run_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Modalità Test (Dry Run)", 
                       variable=self.dry_run_var).pack(anchor='w')
        
        # Backup
        self.backup_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Crea backup prima della rinomina", 
                       variable=self.backup_var).pack(anchor='w')
        
        # Salvataggio log
        log_frame = ttk.Frame(advanced_frame)
        log_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(log_frame, text="Salva log:").pack(side='left')
        self.log_format_var = tk.StringVar(value="none")
        ttk.Combobox(log_frame, textvariable=self.log_format_var, 
                    values=["none", "json", "csv"], state="readonly", width=10).pack(side='left', padx=(5, 0))
    
    def create_preview_tab(self, notebook):
        """
        Crea il tab per l'anteprima e l'esecuzione
        """
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="👁️ Anteprima")
        
        # Bottone per generare anteprima
        preview_button = ttk.Button(frame, text="🔄 Genera Anteprima", command=self.generate_preview)
        preview_button.pack(pady=(0, 10))
        
        # Treeview per l'anteprima
        preview_frame = ttk.LabelFrame(frame, text="Anteprima Modifiche", padding=10)
        preview_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        columns = ('Originale', 'Nuovo', 'Stato')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=15)
        
        # Configurazione colonne
        self.preview_tree.heading('Originale', text='Nome Originale')
        self.preview_tree.heading('Nuovo', text='Nuovo Nome')
        self.preview_tree.heading('Stato', text='Stato')
        
        self.preview_tree.column('Originale', width=350)
        self.preview_tree.column('Nuovo', width=350)
        self.preview_tree.column('Stato', width=100)
        
        # Scrollbar per anteprima
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient='vertical', command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_tree.pack(side='left', fill='both', expand=True)
        preview_scrollbar.pack(side='right', fill='y')
        
        # Frame per i bottoni di esecuzione
        execute_frame = ttk.Frame(frame)
        execute_frame.pack(fill='x', pady=(10, 0))
        
        # Bottone esecuzione
        self.execute_button = ttk.Button(execute_frame, text="▶️ Esegui Rinomina", 
                                       command=self.execute_rename, state='disabled')
        self.execute_button.pack(side='left', padx=(0, 10))
        
        # Bottone annulla
        ttk.Button(execute_frame, text="❌ Annulla", command=self.clear_preview).pack(side='left')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(execute_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side='right', fill='x', expand=True, padx=(10, 0))
    
    def create_log_tab(self, notebook):
        """
        Crea il tab per i log e le statistiche
        """
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📊 Log & Statistiche")
        
        # Sezione statistiche
        stats_frame = ttk.LabelFrame(frame, text="Statistiche", padding=10)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        
        # Etichette per le statistiche
        ttk.Label(stats_grid, text="File processati:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.stats_processed = ttk.Label(stats_grid, text="0", style='Success.TLabel')
        self.stats_processed.grid(row=0, column=1, sticky='w')
        
        ttk.Label(stats_grid, text="Successi:").grid(row=0, column=2, sticky='w', padx=(20, 10))
        self.stats_success = ttk.Label(stats_grid, text="0", style='Success.TLabel')
        self.stats_success.grid(row=0, column=3, sticky='w')
        
        ttk.Label(stats_grid, text="Errori:").grid(row=0, column=4, sticky='w', padx=(20, 10))
        self.stats_errors = ttk.Label(stats_grid, text="0", style='Error.TLabel')
        self.stats_errors.grid(row=0, column=5, sticky='w')
        
        # Area log
        log_frame = ttk.LabelFrame(frame, text="Log Operazioni", padding=10)
        log_frame.pack(fill='both', expand=True)
        
        # Text area con scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Bottoni per gestire i log
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill='x', pady=(5, 0))
        
        ttk.Button(log_buttons, text="🗑️ Pulisci Log", command=self.clear_log).pack(side='left')
        ttk.Button(log_buttons, text="💾 Salva Log", command=self.save_log).pack(side='left', padx=(5, 0))
        ttk.Button(log_buttons, text="📂 Apri Cartella Log", command=self.open_log_folder).pack(side='left', padx=(5, 0))
    
    def create_status_bar(self, parent):
        """
        Crea la barra di stato
        """
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(fill='x', pady=(10, 0))
        
        # Separatore
        ttk.Separator(self.status_bar, orient='horizontal').pack(fill='x', pady=(0, 5))
        
        # Etichetta stato
        self.status_label = ttk.Label(self.status_bar, text="Pronto")
        self.status_label.pack(side='left')
        
        # Etichetta versione
        ttk.Label(self.status_bar, text="v1.0.0").pack(side='right')
    
    def on_rename_type_change(self):
        """
        Gestisce il cambio di tipo di rinomina
        """
        # Pulisce il frame delle opzioni
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Crea le opzioni specifiche per il tipo selezionato
        rename_type = self.rename_type.get()
        
        if rename_type == "sequential":
            self.create_sequential_options()
        elif rename_type == "pattern":
            self.create_pattern_options()
        elif rename_type == "case":
            self.create_case_options()
        elif rename_type == "regex":
            self.create_regex_options()
    
    def create_sequential_options(self):
        """
        Crea le opzioni per rinomina sequenziale
        """
        # Nome base
        base_frame = ttk.Frame(self.options_frame)
        base_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(base_frame, text="Nome base:").pack(side='left')
        self.base_name_var = tk.StringVar(value="file")
        ttk.Entry(base_frame, textvariable=self.base_name_var, width=20).pack(side='left', padx=(5, 10))
        
        # Numero di partenza
        ttk.Label(base_frame, text="Numero iniziale:").pack(side='left')
        self.start_number_var = tk.StringVar(value="1")
        ttk.Entry(base_frame, textvariable=self.start_number_var, width=10).pack(side='left', padx=(5, 0))
        
        # Esempio
        example_label = ttk.Label(self.options_frame, text="Esempio: file_001.txt, file_002.txt, ...", 
                                 foreground='gray')
        example_label.pack(anchor='w', pady=(5, 0))
    
    def create_pattern_options(self):
        """
        Crea le opzioni per pattern personalizzato
        """
        # Pattern
        pattern_frame = ttk.Frame(self.options_frame)
        pattern_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(pattern_frame, text="Pattern:").pack(side='left')
        self.custom_pattern_var = tk.StringVar(value="{name}_{counter}{ext}")
        ttk.Entry(pattern_frame, textvariable=self.custom_pattern_var, width=30).pack(side='left', padx=(5, 0))
        
        # Aiuto per i placeholder
        help_text = ("Placeholder disponibili:\n"
                    "{name} = nome originale\n"
                    "{ext} = estensione\n"
                    "{counter} = numero progressivo\n"
                    "{date} = data (YYYY-MM-DD)\n"
                    "{time} = ora (HH-MM-SS)")
        
        help_label = ttk.Label(self.options_frame, text=help_text, foreground='gray', font=('Courier', 8))
        help_label.pack(anchor='w', pady=(5, 0))
    
    def create_case_options(self):
        """
        Crea le opzioni per trasformazione case
        """
        ttk.Label(self.options_frame, text="Trasformazione:").pack(anchor='w')
        
        self.case_type_var = tk.StringVar(value="lower")
        
        cases = [
            ("Minuscolo", "lower"),
            ("MAIUSCOLO", "upper"),
            ("Titolo", "title"),
            ("camelCase", "camel")
        ]
        
        for text, value in cases:
            ttk.Radiobutton(self.options_frame, text=text, variable=self.case_type_var, 
                           value=value).pack(anchor='w', padx=(10, 0))
    
    def create_regex_options(self):
        """
        Crea le opzioni per regex
        """
        # Pattern regex
        pattern_frame = ttk.Frame(self.options_frame)
        pattern_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(pattern_frame, text="Pattern:").pack(side='left')
        self.regex_pattern_var = tk.StringVar()
        ttk.Entry(pattern_frame, textvariable=self.regex_pattern_var, width=25).pack(side='left', padx=(5, 0))
        
        # Sostituzione
        replace_frame = ttk.Frame(self.options_frame)
        replace_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(replace_frame, text="Sostituisci:").pack(side='left')
        self.regex_replace_var = tk.StringVar()
        ttk.Entry(replace_frame, textvariable=self.regex_replace_var, width=25).pack(side='left', padx=(5, 0))
        
        # Esempio
        example_label = ttk.Label(self.options_frame, 
                                 text="Esempio: IMG_(\\d+) → photo_\\1", 
                                 foreground='gray')
        example_label.pack(anchor='w', pady=(5, 0))
    
    def browse_directory(self):
        """
        Apre il dialog per selezionare una directory
        """
        directory = filedialog.askdirectory(title="Seleziona Directory")
        if directory:
            self.dir_var.set(directory)
            self.selected_directory = directory
            self.update_status("Directory selezionata: " + directory)
    
    def scan_files(self):
        """
        Scansiona i file nella directory selezionata
        """
        directory = self.dir_var.get()
        if not directory:
            messagebox.showwarning("Attenzione", "Seleziona prima una directory!")
            return
        
        pattern = self.pattern_var.get()
        recursive = self.recursive_var.get()
        
        try:
            # Crea il FileRenamer
            self.renamer = FileRenamer(directory, dry_run=True)
            
            # Ottiene i file
            files = self.renamer.get_files(pattern, recursive)
            self.files_to_process = files
            
            # Pulisce la treeview
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
            
            # Popola la treeview
            for file_path in files:
                stat = file_path.stat()
                size = self.format_size(stat.st_size)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                self.files_tree.insert('', 'end', values=(file_path.name, size, modified))
            
            # Aggiorna il contatore
            self.files_count_label.config(text=f"Trovati {len(files)} file")
            self.update_status(f"Trovati {len(files)} file")
            
            # Log
            self.log_message(f"Scansione completata: {len(files)} file trovati")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la scansione: {str(e)}")
            self.log_message(f"Errore scansione: {str(e)}", "ERROR")
    
    def generate_preview(self):
        """
        Genera l'anteprima delle modifiche
        """
        if not self.files_to_process:
            messagebox.showwarning("Attenzione", "Scansiona prima i file!")
            return
        
        try:
            # Genera i nuovi nomi in base al tipo selezionato
            rename_type = self.rename_type.get()
            
            if rename_type == "sequential":
                base_name = self.base_name_var.get()
                start_num = int(self.start_number_var.get())
                self.new_names = self.renamer.rename_sequential(self.files_to_process, base_name, start_num)
            
            elif rename_type == "pattern":
                pattern = self.custom_pattern_var.get()
                self.new_names = self.renamer.rename_with_pattern(self.files_to_process, pattern)
            
            elif rename_type == "case":
                case_type = self.case_type_var.get()
                self.new_names = self.renamer.rename_case_transform(self.files_to_process, case_type)
            
            elif rename_type == "regex":
                regex_pattern = self.regex_pattern_var.get()
                replacement = self.regex_replace_var.get()
                self.new_names = self.renamer.apply_regex_replacement(self.files_to_process, regex_pattern, replacement)
            
            # Pulisce la treeview dell'anteprima
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            
            # Popola l'anteprima
            for original, new_name in zip(self.files_to_process, self.new_names):
                # Verifica se il nuovo nome è valido
                if new_name == original.name:
                    status = "Invariato"
                elif Path(original.parent / new_name).exists():
                    status = "Conflitto"
                else:
                    status = "OK"
                
                self.preview_tree.insert('', 'end', values=(original.name, new_name, status))
            
            # Abilita il bottone di esecuzione
            self.execute_button.config(state='normal')
            self.update_status("Anteprima generata")
            self.log_message("Anteprima generata con successo")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione dell'anteprima: {str(e)}")
            self.log_message(f"Errore anteprima: {str(e)}", "ERROR")
    
    def execute_rename(self):
        """
        Esegue la rinomina dei file
        """
        if not self.new_names:
            messagebox.showwarning("Attenzione", "Genera prima l'anteprima!")
            return
        
        # Conferma dall'utente
        if not self.dry_run_var.get():
            if not messagebox.askyesno("Conferma", "Sei sicuro di voler procedere con la rinomina?"):
                return
        
        # Configura il renamer
        self.renamer.dry_run = self.dry_run_var.get()
        
        # Esegue la rinomina in un thread separato
        thread = threading.Thread(target=self.execute_rename_thread)
        thread.daemon = True
        thread.start()
    
    def execute_rename_thread(self):
        """
        Esegue la rinomina in un thread separato per non bloccare la GUI
        """
        try:
            # Inizializza la progress bar
            self.progress_var.set(0)
            total_files = len(self.files_to_process)
            
            success_count = 0
            error_count = 0
            
            for i, (original_file, new_name) in enumerate(zip(self.files_to_process, self.new_names)):
                try:
                    new_path = original_file.parent / new_name
                    
                    # Verifica conflitti
                    if new_path.exists() and new_path != original_file:
                        self.log_message(f"Conflitto: {new_name} già esistente", "WARNING")
                        error_count += 1
                        continue
                    
                    if not self.renamer.dry_run:
                        # Backup se richiesto
                        if self.backup_var.get():
                            backup_dir = original_file.parent / "backup"
                            backup_dir.mkdir(exist_ok=True)
                            backup_path = backup_dir / original_file.name
                            original_file.copy(backup_path)
                        
                        # Rinomina
                        original_file.rename(new_path)
                        self.log_message(f"Rinominato: {original_file.name} → {new_name}")
                    else:
                        self.log_message(f"[DRY RUN] Rinomina: {original_file.name} → {new_name}")
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    self.log_message(f"Errore rinominando {original_file.name}: {str(e)}", "ERROR")
                
                # Aggiorna progress bar
                progress = ((i + 1) / total_files) * 100
                self.progress_var.set(progress)
            
            # Aggiorna statistiche
            self.update_stats(success_count, error_count, total_files)
            
            # Salva log se richiesto
            if self.log_format_var.get() != "none":
                self.renamer.save_operations_log(self.log_format_var.get())
            
            # Messaggio finale
            if error_count == 0:
                self.log_message(f"✅ Operazione completata con successo! {success_count} file processati", "SUCCESS")
                if not self.dry_run_var.get():
                    messagebox.showinfo("Successo", f"Rinomina completata!\n{success_count} file processati")
            else:
                self.log_message(f"⚠️ Operazione completata con {error_count} errori", "WARNING")
                messagebox.showwarning("Attenzione", f"Operazione completata con {error_count} errori.\nControlla il log per i dettagli.")
            
            self.update_status("Operazione completata")
            
        except Exception as e:
            self.log_message(f"Errore durante l'esecuzione: {str(e)}", "ERROR")
            messagebox.showerror("Errore", f"Errore durante l'esecuzione: {str(e)}")
    
    def clear_preview(self):
        """
        Pulisce l'anteprima e resetta lo stato
        """
        # Pulisce la treeview dell'anteprima
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Resetta le variabili
        self.new_names = []
        self.execute_button.config(state='disabled')
        self.progress_var.set(0)
        
        self.update_status("Anteprima pulita")
        self.log_message("Anteprima pulita")
    
    def update_stats(self, processed: int, errors: int, total: int):
        """
        Aggiorna le statistiche mostrate nell'interfaccia
        """
        success = processed - errors
        
        self.stats_processed.config(text=str(total))
        self.stats_success.config(text=str(success))
        self.stats_errors.config(text=str(errors))
    
    def log_message(self, message: str, level: str = "INFO"):
        """
        Aggiunge un messaggio al log
        
        Args:
            message: Il messaggio da loggare
            level: Livello del messaggio (INFO, WARNING, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Definisce i colori per i diversi livelli
        colors = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
            "SUCCESS": "green"
        }
        
        # Formatta il messaggio
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        # Aggiunge al log text widget
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)  # Scrolla alla fine
        
        # Colora il messaggio
        line_start = f"{self.log_text.index(tk.END)}-1l"
        line_end = f"{self.log_text.index(tk.END)}-1c"
        
        if level in colors:
            tag_name = f"color_{level}"
            self.log_text.tag_config(tag_name, foreground=colors[level])
            self.log_text.tag_add(tag_name, line_start, line_end)
    
    def clear_log(self):
        """
        Pulisce il log
        """
        self.log_text.delete(1.0, tk.END)
        self.update_status("Log pulito")
    
    def save_log(self):
        """
        Salva il log in un file
        """
        content = self.log_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showinfo("Info", "Il log è vuoto!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Salva Log",
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Successo", f"Log salvato in: {filename}")
                self.log_message(f"Log salvato in: {filename}")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante il salvataggio: {str(e)}")
    
    def open_log_folder(self):
        """
        Apre la cartella dei log
        """
        log_dir = Path("logs")
        if not log_dir.exists():
            log_dir.mkdir()
        
        # Apre la cartella con il file manager del sistema
        try:
            if sys.platform == "win32":
                os.startfile(str(log_dir))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(log_dir)])
            else:
                subprocess.run(["xdg-open", str(log_dir)])
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire la cartella: {str(e)}")
    
    def update_status(self, message: str):
        """
        Aggiorna la barra di stato
        """
        self.status_label.config(text=message)
    
    def format_size(self, size_bytes: int) -> str:
        """
        Formatta la dimensione del file in modo leggibile
        
        Args:
            size_bytes: Dimensione in bytes
            
        Returns:
            Stringa formattata (es. "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def save_settings(self):
        """
        Salva le impostazioni dell'applicazione
        """
        settings = {
            'last_directory': self.dir_var.get(),
            'pattern': self.pattern_var.get(),
            'recursive': self.recursive_var.get(),
            'rename_type': self.rename_type.get(),
            'dry_run': self.dry_run_var.get(),
            'backup': self.backup_var.get(),
            'log_format': self.log_format_var.get()
        }
        
        # Aggiunge le impostazioni specifiche per tipo
        if hasattr(self, 'base_name_var'):
            settings['base_name'] = self.base_name_var.get()
        if hasattr(self, 'start_number_var'):
            settings['start_number'] = self.start_number_var.get()
        if hasattr(self, 'custom_pattern_var'):
            settings['custom_pattern'] = self.custom_pattern_var.get()
        if hasattr(self, 'case_type_var'):
            settings['case_type'] = self.case_type_var.get()
        if hasattr(self, 'regex_pattern_var'):
            settings['regex_pattern'] = self.regex_pattern_var.get()
        if hasattr(self, 'regex_replace_var'):
            settings['regex_replace'] = self.regex_replace_var.get()
        
        try:
            with open('gui_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            self.log_message(f"Errore salvando le impostazioni: {str(e)}", "ERROR")
    
    def load_settings(self):
        """
        Carica le impostazioni salvate
        """
        try:
            if os.path.exists('gui_settings.json'):
                with open('gui_settings.json', 'r') as f:
                    settings = json.load(f)
                
                # Ripristina le impostazioni base
                if 'last_directory' in settings:
                    self.dir_var.set(settings['last_directory'])
                if 'pattern' in settings:
                    self.pattern_var.set(settings['pattern'])
                if 'recursive' in settings:
                    self.recursive_var.set(settings['recursive'])
                if 'rename_type' in settings:
                    self.rename_type.set(settings['rename_type'])
                if 'dry_run' in settings:
                    self.dry_run_var.set(settings['dry_run'])
                if 'backup' in settings:
                    self.backup_var.set(settings['backup'])
                if 'log_format' in settings:
                    self.log_format_var.set(settings['log_format'])
                
                self.log_message("Impostazioni caricate")
        except Exception as e:
            self.log_message(f"Errore caricando le impostazioni: {str(e)}", "ERROR")
    
    def on_closing(self):
        """
        Gestisce la chiusura dell'applicazione
        """
        # Salva le impostazioni
        self.save_settings()
        
        # Chiude l'applicazione
        self.root.destroy()


class AboutDialog:
    """
    Dialog per mostrare informazioni sull'applicazione
    """
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Informazioni")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        # Centra la finestra
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Contenuto
        content = ttk.Frame(self.dialog, padding=20)
        content.pack(fill='both', expand=True)
        
        # Titolo
        title = ttk.Label(content, text="🔄 Advanced File Renamer", 
                         font=('Helvetica', 16, 'bold'))
        title.pack(pady=(0, 10))
        
        # Versione
        version = ttk.Label(content, text="Versione 1.0.0", 
                           font=('Helvetica', 10))
        version.pack(pady=(0, 10))
        
        # Descrizione
        description = tk.Text(content, height=8, width=50, wrap=tk.WORD)
        description.pack(pady=(0, 10))
        
        desc_text = """Un potente strumento per rinominare file in batch con interfaccia grafica intuitiva.

Caratteristiche:
• Rinomina sequenziale con numerazione automatica
• Pattern personalizzati con placeholder
• Trasformazioni di case (maiuscolo/minuscolo)
• Supporto per espressioni regolari
• Anteprima delle modifiche
• Modalità test (dry run)
• Backup automatico
• Log dettagliato delle operazioni

Sviluppato con Python e tkinter."""
        
        description.insert(1.0, desc_text)
        description.config(state='disabled')
        
        # Bottone chiudi
        ttk.Button(content, text="Chiudi", command=self.dialog.destroy).pack()


def create_menu(root, gui):
    """
    Crea il menu principale dell'applicazione
    
    Args:
        root: Finestra principale
        gui: Istanza della GUI
    """
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # Menu File
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Apri Directory...", command=gui.browse_directory)
    file_menu.add_separator()
    file_menu.add_command(label="Salva Impostazioni", command=gui.save_settings)
    file_menu.add_command(label="Carica Impostazioni", command=gui.load_settings)
    file_menu.add_separator()
    file_menu.add_command(label="Esci", command=gui.on_closing)
    
    # Menu Strumenti
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Strumenti", menu=tools_menu)
    tools_menu.add_command(label="Pulisci Log", command=gui.clear_log)
    tools_menu.add_command(label="Apri Cartella Log", command=gui.open_log_folder)
    tools_menu.add_separator()
    tools_menu.add_command(label="Pulisci Anteprima", command=gui.clear_preview)
    
    # Menu Aiuto
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Aiuto", menu=help_menu)
    help_menu.add_command(label="Informazioni", command=lambda: AboutDialog(root))


def main():
    """
    Funzione principale che avvia l'applicazione GUI
    """
    # Crea la finestra principale
    root = tk.Tk()
    
    # Crea l'interfaccia
    gui = FileRenamerGUI(root)
    
    # Crea il menu
    create_menu(root, gui)
    
    # Gestisce la chiusura
    root.protocol("WM_DELETE_WINDOW", gui.on_closing)
    
    # Messaggio di benvenuto
    gui.log_message("🚀 File Renamer GUI avviato", "SUCCESS")
    gui.log_message("Seleziona una directory e scansiona i file per iniziare", "INFO")
    
    # Avvia l'applicazione
    root.mainloop()


if __name__ == "__main__":
    main()