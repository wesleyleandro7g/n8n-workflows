#!/usr/bin/env python3
"""
Generate Translations for All Workflows
Pre-generates translations for all workflows to populate the cache
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.translation_service import get_translation_service
from workflow_db import WorkflowDatabase
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_all_translations(batch_size: int = 50):
    """
    Generate translations for all workflows in all supported languages
    
    Args:
        batch_size: Number of workflows to process before showing progress
    """
    logger.info("🌍 Starting translation generation...")
    
    # Initialize services
    db = WorkflowDatabase()
    translation_service = get_translation_service()
    
    # Get all workflows
    logger.info("📊 Fetching workflows from database...")
    workflows, total = db.search_workflows(query="", limit=10000)
    
    if total == 0:
        logger.warning("⚠️  No workflows found in database. Please index workflows first.")
        return
    
    logger.info(f"✅ Found {total} workflows to translate")
    
    # Languages to translate to (excluding English which is the source)
    target_languages = ['pt-br', 'es']
    
    total_translations = 0
    
    for lang in target_languages:
        logger.info(f"\n{'='*60}")
        logger.info(f"🌐 Generating {lang.upper()} translations...")
        logger.info(f"{'='*60}\n")
        
        # Use tqdm for progress bar
        with tqdm(total=len(workflows), desc=f"Translating to {lang.upper()}", 
                  unit="workflow", ncols=100) as pbar:
            
            for i, workflow in enumerate(workflows):
                try:
                    # Translate workflow (this will cache translations)
                    translation_service.translate_workflow(workflow, lang)
                    total_translations += 1
                    
                    pbar.update(1)
                    
                    # Show sample translations for first few workflows
                    if i < 3:
                        logger.info(f"\n📝 Sample translation for {workflow.get('filename', 'unknown')}:")
                        logger.info(f"   EN: {workflow.get('name', 'N/A')[:50]}...")
                        translated = translation_service.get_translation(
                            workflow.get('filename', ''),
                            'name',
                            workflow.get('name', ''),
                            lang
                        )
                        logger.info(f"   {lang.upper()}: {translated[:50]}...\n")
                    
                except Exception as e:
                    logger.error(f"Error translating {workflow.get('filename', 'unknown')}: {e}")
                    continue
        
        logger.info(f"✅ Completed {lang.upper()} translations")
    
    # Show final statistics
    logger.info(f"\n{'='*60}")
    logger.info("📊 Translation Generation Complete!")
    logger.info(f"{'='*60}\n")
    
    stats = translation_service.get_cache_stats()
    logger.info(f"Total translations cached: {stats['total']}")
    logger.info(f"By language:")
    for lang, count in stats['by_language'].items():
        logger.info(f"  • {lang.upper()}: {count} translations")
    
    logger.info(f"\n✨ All translations have been generated and cached!")
    logger.info(f"🚀 The API will now serve translated content instantly!")


def clear_and_regenerate():
    """Clear all translations and regenerate from scratch"""
    logger.info("🗑️  Clearing existing translations...")
    
    translation_service = get_translation_service()
    deleted = translation_service.clear_cache()
    
    logger.info(f"✅ Cleared {deleted} translations")
    logger.info("🔄 Regenerating translations...\n")
    
    generate_all_translations()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate translations for N8N workflows'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing translations before regenerating'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of workflows to process in each batch (default: 50)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current translation statistics only'
    )
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            # Just show statistics
            translation_service = get_translation_service()
            stats = translation_service.get_cache_stats()
            
            print("\n📊 Translation Cache Statistics")
            print("="*60)
            print(f"Total translations: {stats['total']}")
            print(f"\nBy language:")
            for lang, count in stats['by_language'].items():
                print(f"  • {lang.upper()}: {count} translations")
            
            if stats['top_workflows']:
                print(f"\nTop workflows by translations:")
                for filename, count in stats['top_workflows'][:5]:
                    print(f"  • {filename}: {count} translations")
            print()
            
        elif args.clear:
            clear_and_regenerate()
        else:
            generate_all_translations(batch_size=args.batch_size)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Translation generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error during translation generation: {e}")
        sys.exit(1)
