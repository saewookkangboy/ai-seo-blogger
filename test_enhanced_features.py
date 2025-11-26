
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.routers.blog_generator import generate_post_enhanced, generate_post_enhanced_gemini_2_flash
from app.schemas import PostRequest
from app.services.content_generator import create_enhanced_blog_post

@pytest.mark.asyncio
async def test_generate_post_enhanced_endpoint():
    # Mock dependencies
    mock_db = MagicMock()
    mock_req = PostRequest(text="Test content for enhanced mode", ai_mode="enhanced")
    
    # Mock create_enhanced_blog_post result
    mock_result = {
        'post': '<h1>Test Title</h1><p>Test Content</p>',
        'title': 'Test Title',
        'meta_description': 'Test Meta',
        'keywords': 'test, content',
        'word_count': 100,
        'ai_analysis': {
            'trust_score': 5,
            'seo_score': 10,
            'ai_summary': 'Test Summary'
        },
        'guidelines_analysis': {}
    }
    
    with patch('app.services.content_generator.create_enhanced_blog_post', return_value=mock_result) as mock_create:
        with patch('app.crud.create_blog_post') as mock_db_create:
            mock_db_create.return_value.id = 1
            mock_db_create.return_value.title = "Test Title"
            mock_db_create.return_value.content_html = "<h1>Test Title</h1><p>Test Content</p>"
            mock_db_create.return_value.keywords = "test, content"
            mock_db_create.return_value.original_url = "Test URL"
            mock_db_create.return_value.created_at.isoformat.return_value = "2023-01-01T00:00:00"
            
            # Call endpoint
            response = await generate_post_enhanced(mock_req, mock_db)
            
            # Verify response
            assert response.success is True
            assert response.data['ai_analysis']['trust_score'] == 5
            assert response.data['ai_analysis']['seo_score'] == 10
            assert response.data['ai_mode'] == "enhanced"
            
            # Verify mock call
            mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_post_enhanced_gemini_endpoint():
    # Mock dependencies
    mock_db = MagicMock()
    mock_req = PostRequest(text="Test content for gemini enhanced", ai_mode="enhanced_gemini")
    
    # Mock create_enhanced_blog_post result
    mock_result = {
        'post': '<h1>Gemini Title</h1>',
        'title': 'Gemini Title',
        'meta_description': 'Gemini Meta',
        'keywords': 'gemini, test',
        'word_count': 100,
        'ai_analysis': {
            'trust_score': 5,
            'seo_score': 10,
            'ai_summary': 'Gemini Summary'
        },
        'guidelines_analysis': {}
    }
    
    with patch('app.services.content_generator.create_enhanced_blog_post', return_value=mock_result) as mock_create:
        with patch('app.crud.create_blog_post') as mock_db_create:
            mock_db_create.return_value.id = 2
            mock_db_create.return_value.title = "Gemini Title"
            mock_db_create.return_value.content_html = "<h1>Gemini Title</h1>"
            mock_db_create.return_value.keywords = "gemini, test"
            mock_db_create.return_value.original_url = "Test URL"
            mock_db_create.return_value.created_at.isoformat.return_value = "2023-01-01T00:00:00"
            
            # Call endpoint
            response = await generate_post_enhanced_gemini_2_flash(mock_req, mock_db)
            
            # Verify response
            assert response.success is True
            assert response.data['ai_analysis']['trust_score'] == 5
            assert response.data['ai_mode'] == "gemini_2_0_flash"  # Should be set to gemini mode
            
            # Verify mock call with correct mode
            args, kwargs = mock_create.call_args
            assert kwargs['ai_mode'] == "gemini_2_0_flash"
