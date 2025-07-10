#!/usr/bin/env python3
"""
Advanced File Renamer CLI Tool
==============================

Un potente strumento da linea di comando per rinominare file in batch
con diverse regole e opzioni di formattazione.

Autore: GangstaVik
Versione: 1.0.0
"""

import argparse
import os
import sys
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Optional, Tuple
import shutil

# Librerie esterne per migliorare l'UX
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich non installato. Installa con: pip install rich")

# Configurazione del logging
def setup_logging(log_level: str = "INFO") -> None:
    """
    Configura il sistema di logging per tracciare tutte le operazioni
    
    Args:
        log_level: Livello di log (DEBUG, INFO, WARNING, ERROR)
    """
    # Crea la directory logs se non esiste
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Nome del file log con timestamp
    log_file = log_dir / f"file_renamer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configurazione del logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Anche su console
        ]
    )


class FileRenamer:
    """
    Classe principale per gestire la rinomina dei file
    
    Questa classe incapsula tutta la logica di rinomina, fornendo
    diversi metodi per applicare regole di denominazione ai file.
    """
    
    def __init__(self, directory: str, dry_run: bool = False):
        """
        Inizializza il file renamer
        
        Args:
            directory: Directory di lavoro dove cercare i file
            dry_run: Se True, simula le operazioni senza eseguirle
        """
        self.directory = Path(directory)
        self.dry_run = dry_run
        self.console = Console() if RICH_AVAILABLE else None
        self.operations_log = []  # Tiene traccia delle operazioni
        
        # Verifica che la directory esista
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory non trovata: {directory}")
        
        logging.info(f"FileRenamer inizializzato per directory: {directory}")
    
    def get_files(self, pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        Ottiene la lista dei file che corrispondono al pattern
        
        Args:
            pattern: Pattern di ricerca (es. "*.txt", "image_*")
            recursive: Se True, cerca anche nelle sottodirectory
            
        Returns:
            Lista dei file trovati
        """
        if recursive:
            files = list(self.directory.rglob(pattern))
        else:
            files = list(self.directory.glob(pattern))
        
        # Filtra solo i file (non le directory)
        files = [f for f in files if f.is_file()]
        
        logging.info(f"Trovati {len(files)} file con pattern '{pattern}'")
        return files
    
    def preview_changes(self, files: List[Path], new_names: List[str]) -> None:
        """
        Mostra un'anteprima delle modifiche che verranno apportate
        
        Args:
            files: Lista dei file originali
            new_names: Lista dei nuovi nomi
        """
        if RICH_AVAILABLE:
            table = Table(title="Anteprima Modifiche")
            table.add_column("File Originale", style="cyan")
            table.add_column("Nuovo Nome", style="green")
            table.add_column("Dimensione", style="yellow")
            
            for original, new_name in zip(files, new_names):
                size = self._format_size(original.stat().st_size)
                table.add_row(original.name, new_name, size)
            
            self.console.print(table)
        else:
            print("\n📋 ANTEPRIMA MODIFICHE:")
            print("-" * 60)
            for original, new_name in zip(files, new_names):
                size = self._format_size(original.stat().st_size)
                print(f"{original.name:<30} → {new_name:<30} ({size})")
    
    def _format_size(self, size_bytes: int) -> str:
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
    
    def rename_with_pattern(self, files: List[Path], pattern: str) -> List[str]:
        """
        Genera nuovi nomi usando un pattern personalizzato
        
        Pattern supportati:
        - {name}: nome originale senza estensione
        - {ext}: estensione originale
        - {counter}: numero progressivo
        - {date}: data corrente (YYYY-MM-DD)
        - {time}: ora corrente (HH-MM-SS)
        - {size}: dimensione del file
        
        Args:
            files: Lista dei file da rinominare
            pattern: Pattern per i nuovi nomi
            
        Returns:
            Lista dei nuovi nomi generati
        """
        new_names = []
        
        for i, file_path in enumerate(files, 1):
            # Estrae informazioni dal file
            name_without_ext = file_path.stem
            extension = file_path.suffix
            file_size = self._format_size(file_path.stat().st_size)
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H-%M-%S')
            
            # Sostituisce i placeholder nel pattern
            new_name = pattern.format(
                name=name_without_ext,
                ext=extension,
                counter=str(i).zfill(3),  # Pad con zeri (001, 002, etc.)
                date=current_date,
                time=current_time,
                size=file_size
            )
            
            new_names.append(new_name)
        
        return new_names
    
    def rename_sequential(self, files: List[Path], base_name: str, start_num: int = 1) -> List[str]:
        """
        Rinomina i file in sequenza numerica
        
        Args:
            files: Lista dei file da rinominare
            base_name: Nome base per i file
            start_num: Numero di partenza
            
        Returns:
            Lista dei nuovi nomi
        """
        new_names = []
        
        for i, file_path in enumerate(files):
            extension = file_path.suffix
            number = start_num + i
            new_name = f"{base_name}_{number:03d}{extension}"
            new_names.append(new_name)
        
        return new_names
    
    def rename_case_transform(self, files: List[Path], transform: str) -> List[str]:
        """
        Trasforma il case dei nomi file
        
        Args:
            files: Lista dei file da rinominare
            transform: Tipo di trasformazione (lower, upper, title, camel)
            
        Returns:
            Lista dei nuovi nomi
        """
        new_names = []
        
        for file_path in files:
            name_without_ext = file_path.stem
            extension = file_path.suffix
            
            if transform == "lower":
                new_name = name_without_ext.lower()
            elif transform == "upper":
                new_name = name_without_ext.upper()
            elif transform == "title":
                new_name = name_without_ext.title()
            elif transform == "camel":
                # Converte in camelCase
                words = re.split(r'[_\-\s]+', name_without_ext)
                new_name = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
            else:
                new_name = name_without_ext
            
            new_names.append(new_name + extension)
        
        return new_names
    
    def apply_regex_replacement(self, files: List[Path], pattern: str, replacement: str) -> List[str]:
        """
        Applica una sostituzione regex ai nomi dei file
        
        Args:
            files: Lista dei file da rinominare
            pattern: Pattern regex da cercare
            replacement: Stringa di sostituzione
            
        Returns:
            Lista dei nuovi nomi
        """
        new_names = []
        
        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Pattern regex non valido: {e}")
        
        for file_path in files:
            original_name = file_path.name
            new_name = compiled_pattern.sub(replacement, original_name)
            new_names.append(new_name)
        
        return new_names
    
    def execute_rename(self, files: List[Path], new_names: List[str]) -> bool:
        """
        Esegue effettivamente la rinomina dei file
        
        Args:
            files: Lista dei file da rinominare
            new_names: Lista dei nuovi nomi
            
        Returns:
            True se tutte le operazioni sono riuscite
        """
        success_count = 0
        
        if RICH_AVAILABLE:
            progress = Progress()
            task = progress.add_task("Rinomina file...", total=len(files))
            progress.start()
        
        for original_file, new_name in zip(files, new_names):
            try:
                new_path = original_file.parent / new_name
                
                # Verifica che il nuovo nome non esista già
                if new_path.exists() and new_path != original_file:
                    logging.warning(f"File già esistente: {new_name}")
                    continue
                
                if not self.dry_run:
                    # Esegue la rinomina
                    original_file.rename(new_path)
                    logging.info(f"Rinominato: {original_file.name} → {new_name}")
                else:
                    logging.info(f"[DRY RUN] Rinomina: {original_file.name} → {new_name}")
                
                # Salva l'operazione nel log
                self.operations_log.append({
                    'original': str(original_file),
                    'new': str(new_path),
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
                
                success_count += 1
                
                if RICH_AVAILABLE:
                    progress.update(task, advance=1)
            
            except Exception as e:
                logging.error(f"Errore rinominando {original_file.name}: {e}")
                self.operations_log.append({
                    'original': str(original_file),
                    'new': new_name,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
        
        if RICH_AVAILABLE:
            progress.stop()
        
        return success_count == len(files)
    
    def save_operations_log(self, format_type: str = "json") -> None:
        """
        Salva il log delle operazioni in un file
        
        Args:
            format_type: Formato del file (json, csv)
        """
        if not self.operations_log:
            return
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == "json":
            log_file = log_dir / f"operations_log_{timestamp}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.operations_log, f, indent=2, ensure_ascii=False)
        
        elif format_type == "csv":
            log_file = log_dir / f"operations_log_{timestamp}.csv"
            with open(log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['original', 'new', 'timestamp', 'success', 'error'])
                writer.writeheader()
                writer.writerows(self.operations_log)
        
        logging.info(f"Log operazioni salvato in: {log_file}")


def create_cli_parser() -> argparse.ArgumentParser:
    """
    Crea e configura il parser per gli argomenti della command line
    
    Returns:
        Parser configurato
    """
    parser = argparse.ArgumentParser(
        description="🔄 Advanced File Renamer - Strumento per rinominare file in batch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  %(prog)s -d /path/to/files -p "*.jpg" --sequential "photo"
  %(prog)s -d . -p "*.txt" --pattern "doc_{counter}_{date}{ext}"
  %(prog)s -d /images --case lower --recursive
  %(prog)s -d . --regex "IMG_(\d+)" --replacement "photo_\\1"
        """
    )
    
    # Argomenti principali
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default='.',
        help='Directory di lavoro (default: directory corrente)'
    )
    
    parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='*',
        help='Pattern per selezionare i file (default: *)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Cerca file ricorsivamente nelle sottodirectory'
    )
    
    # Modalità di rinomina (mutualmente esclusive)
    rename_group = parser.add_mutually_exclusive_group(required=True)
    
    rename_group.add_argument(
        '--sequential',
        type=str,
        help='Rinomina sequenziale con nome base specificato'
    )
    
    rename_group.add_argument(
        '--custom-pattern',
        type=str,
        help='Pattern personalizzato (usa {name}, {ext}, {counter}, {date}, {time})'
    )
    
    rename_group.add_argument(
        '--case',
        choices=['lower', 'upper', 'title', 'camel'],
        help='Trasforma il case dei nomi file'
    )
    
    rename_group.add_argument(
        '--regex',
        type=str,
        help='Pattern regex da sostituire (usa con --replacement)'
    )
    
    # Opzioni aggiuntive
    parser.add_argument(
        '--replacement',
        type=str,
        help='Stringa di sostituzione per --regex'
    )
    
    parser.add_argument(
        '--start-number',
        type=int,
        default=1,
        help='Numero di partenza per rinomina sequenziale (default: 1)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula le operazioni senza eseguirle'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Livello di logging (default: INFO)'
    )
    
    parser.add_argument(
        '--save-log',
        choices=['json', 'csv'],
        help='Salva il log delle operazioni nel formato specificato'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def main():
    """
    Funzione principale del programma
    
    Questa funzione:
    1. Analizza gli argomenti della command line
    2. Configura il logging
    3. Crea il FileRenamer
    4. Esegue le operazioni richieste
    """
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Configura il logging
    setup_logging(args.log_level)
    
    # Validazione argomenti
    if args.regex and not args.replacement:
        print("❌ Errore: --regex richiede --replacement")
        sys.exit(1)
    
    try:
        # Crea il FileRenamer
        renamer = FileRenamer(args.directory, dry_run=args.dry_run)
        
        # Ottiene i file da processare
        files = renamer.get_files(args.pattern, args.recursive)
        
        if not files:
            print(f"⚠️  Nessun file trovato con pattern '{args.pattern}'")
            sys.exit(0)
        
        # Genera i nuovi nomi in base alla modalità scelta
        if args.sequential:
            new_names = renamer.rename_sequential(files, args.sequential, args.start_number)
        elif args.custom_pattern:
            new_names = renamer.rename_with_pattern(files, args.custom_pattern)
        elif args.case:
            new_names = renamer.rename_case_transform(files, args.case)
        elif args.regex:
            new_names = renamer.apply_regex_replacement(files, args.regex, args.replacement)
        
        # Mostra l'anteprima
        renamer.preview_changes(files, new_names)
        
        # Conferma dell'utente (solo se non è dry run)
        if not args.dry_run:
            if RICH_AVAILABLE:
                console = Console()
                confirm = console.input("\n❓ Procedere con la rinomina? [y/N]: ")
            else:
                confirm = input("\n❓ Procedere con la rinomina? [y/N]: ")
            
            if confirm.lower() not in ['y', 'yes', 'si', 's']:
                print("✋ Operazione annullata")
                sys.exit(0)
        
        # Esegue la rinomina
        success = renamer.execute_rename(files, new_names)
        
        if success:
            print(f"✅ Rinominati con successo {len(files)} file!")
        else:
            print("⚠️  Alcune operazioni potrebbero non essere riuscite. Controlla i log.")
        
        # Salva il log se richiesto
        if args.save_log:
            renamer.save_operations_log(args.save_log)
    
    except KeyboardInterrupt:
        print("\n🛑 Operazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Errore durante l'esecuzione: {e}")
        print(f"❌ Errore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()