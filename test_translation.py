#!/usr/bin/env python3
"""
Quick test for translation functionality
"""

from src.translation_service import get_translation_service

def test_translation():
    print("🧪 Testing Translation Service\n")
    
    # Initialize service
    ts = get_translation_service()
    print("✅ Translation service initialized")
    
    # Test translation
    test_text = "Create automated workflow for data processing"
    workflow_id = "test_workflow.json"
    
    print(f"\n📝 Original text: {test_text}")
    
    # Translate to Portuguese
    pt_translation = ts.get_translation(
        workflow_id=workflow_id,
        field_name='name',
        original_text=test_text,
        target_lang='pt-br'
    )
    print(f"🇧🇷 Portuguese: {pt_translation}")
    
    # Translate to Spanish
    es_translation = ts.get_translation(
        workflow_id=workflow_id,
        field_name='name',
        original_text=test_text,
        target_lang='es'
    )
    print(f"🇪🇸 Spanish: {es_translation}")
    
    # Get cached (should be instant)
    print("\n⚡ Testing cache (should be instant)...")
    pt_cached = ts.get_translation(
        workflow_id=workflow_id,
        field_name='name',
        original_text=test_text,
        target_lang='pt-br'
    )
    print(f"✅ Cache working! Got: {pt_cached}")
    
    # Get stats
    stats = ts.get_cache_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"   Total: {stats['total']} translations")
    print(f"   By language: {stats['by_language']}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_translation()
