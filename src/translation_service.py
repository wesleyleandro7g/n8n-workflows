"""
Translation Service with Cache
Provides automatic translation for workflow metadata with database caching
Supports: English (en), Portuguese-BR (pt-br), Spanish (es)
"""

import sqlite3
from typing import Dict, Optional, List
import logging
from datetime import datetime

try:
    from googletrans import Translator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logging.warning("googletrans not installed. Translation will be disabled.")


class TranslationService:
    """
    Translation service with SQLite cache for workflow metadata
    
    Features:
    - Automatic translation using Google Translate
    - SQLite cache to avoid repeated API calls
    - Fallback to original text if translation fails
    - Support for multiple languages
    """
    
    SUPPORTED_LANGUAGES = ['en', 'pt', 'es']
    DEFAULT_LANGUAGE = 'en'
    
    # Fields that should be translated in workflow objects
    TRANSLATABLE_FIELDS = ['name', 'description']
    
    def __init__(self, db_path: str = "workflows.db"):
        """
        Initialize translation service
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.translator = Translator() if TRANSLATION_AVAILABLE else None
        self.logger = logging.getLogger(__name__)
        self._create_translation_table()
    
    def _create_translation_table(self):
        """Create translations table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    workflow_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    language TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (workflow_id, field_name, language)
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_translations_lookup 
                ON translations(workflow_id, language)
            """)
            
            conn.commit()
            conn.close()
            self.logger.info("Translation table initialized successfully")
        except Exception as e:
            self.logger.error(f"Error creating translation table: {e}")
    
    def get_translation(self, workflow_id: str, field_name: str, 
                       original_text: str, target_lang: str) -> str:
        """
        Get translation from cache or generate new one
        
        Args:
            workflow_id: Workflow identifier (filename)
            field_name: Field being translated (name, description, etc.)
            original_text: Original text to translate
            target_lang: Target language code (en, pt-br, es)
            
        Returns:
            Translated text or original if translation fails
        """
        # If target is English or no text, return original
        if target_lang == 'en' or not original_text or not original_text.strip():
            return original_text
        
        # Validate language
        if target_lang not in self.SUPPORTED_LANGUAGES:
            self.logger.warning(f"Unsupported language: {target_lang}, using original")
            return original_text
        
        # Check if translation is available
        if not TRANSLATION_AVAILABLE or not self.translator:
            return original_text
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to get cached translation
            cursor.execute("""
                SELECT translated_text FROM translations
                WHERE workflow_id = ? AND field_name = ? AND language = ?
            """, (workflow_id, field_name, target_lang))
            
            result = cursor.fetchone()
            
            if result:
                conn.close()
                return result[0]
            
            # Generate new translation
            self.logger.debug(f"Translating {field_name} for {workflow_id} to {target_lang}")
            
            # Use language code directly
            lang_code = target_lang
            
            translated = self.translator.translate(
                original_text,
                src='en',
                dest=lang_code
            ).text
            
            # Cache the translation
            cursor.execute("""
                INSERT OR REPLACE INTO translations 
                (workflow_id, field_name, language, original_text, translated_text, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (workflow_id, field_name, target_lang, original_text, translated, datetime.now()))
            
            conn.commit()
            conn.close()
            
            return translated
            
        except Exception as e:
            self.logger.error(f"Translation error for {workflow_id}.{field_name}: {e}")
            if 'conn' in locals():
                conn.close()
            return original_text  # Fallback to original
    
    def translate_workflow(self, workflow: Dict, target_lang: str) -> Dict:
        """
        Translate workflow metadata fields
        
        Args:
            workflow: Workflow dictionary with metadata
            target_lang: Target language code
            
        Returns:
            Workflow dictionary with translated fields
        """
        if target_lang == 'en':
            return workflow  # No translation needed for English
        
        translated = workflow.copy()
        workflow_id = workflow.get('filename', 'unknown')
        
        # Translate each translatable field
        for field in self.TRANSLATABLE_FIELDS:
            if field in workflow and workflow[field]:
                translated[field] = self.get_translation(
                    workflow_id,
                    field,
                    workflow[field],
                    target_lang
                )
        
        # Add language metadata
        translated['_language'] = target_lang
        
        return translated
    
    def translate_workflows(self, workflows: List[Dict], target_lang: str) -> List[Dict]:
        """
        Translate multiple workflows
        
        Args:
            workflows: List of workflow dictionaries
            target_lang: Target language code
            
        Returns:
            List of translated workflow dictionaries
        """
        if target_lang == 'en':
            return workflows
        
        return [self.translate_workflow(w, target_lang) for w in workflows]
    
    def clear_cache(self, workflow_id: Optional[str] = None, language: Optional[str] = None):
        """
        Clear translation cache
        
        Args:
            workflow_id: If provided, clear only for this workflow
            language: If provided, clear only for this language
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if workflow_id and language:
                cursor.execute(
                    "DELETE FROM translations WHERE workflow_id = ? AND language = ?",
                    (workflow_id, language)
                )
            elif workflow_id:
                cursor.execute(
                    "DELETE FROM translations WHERE workflow_id = ?",
                    (workflow_id,)
                )
            elif language:
                cursor.execute(
                    "DELETE FROM translations WHERE language = ?",
                    (language,)
                )
            else:
                cursor.execute("DELETE FROM translations")
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared {deleted} cached translations")
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """
        Get translation cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total translations
            cursor.execute("SELECT COUNT(*) FROM translations")
            total = cursor.fetchone()[0]
            
            # By language
            cursor.execute("""
                SELECT language, COUNT(*) 
                FROM translations 
                GROUP BY language
            """)
            by_language = dict(cursor.fetchall())
            
            # By workflow (top 10)
            cursor.execute("""
                SELECT workflow_id, COUNT(*) as count
                FROM translations 
                GROUP BY workflow_id
                ORDER BY count DESC
                LIMIT 10
            """)
            top_workflows = cursor.fetchall()
            
            conn.close()
            
            return {
                'total': total,
                'by_language': by_language,
                'top_workflows': top_workflows
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {'total': 0, 'by_language': {}, 'top_workflows': []}


# Global instance
_translation_service = None

def get_translation_service(db_path: str = "workflows.db") -> TranslationService:
    """Get or create global translation service instance"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService(db_path)
    return _translation_service
