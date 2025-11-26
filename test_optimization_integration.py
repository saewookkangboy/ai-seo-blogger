import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from app.services.content_generator import create_blog_post

@pytest.mark.asyncio
async def test_optimization_integration():
    # Mock Redis Cache
    mock_redis = MagicMock()
    mock_redis.get.return_value = None  # Cache miss
    
    # Mock OpenAI Client
    mock_openai_client = AsyncMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = json.dumps({
        "title": "Test Title",
        "meta_description": "Test Description",
        "content": "<h1>Test Content</h1>",
        "keywords": "test, keywords",
        "metrics": {},
        "score": 90,
        "evaluation": "Good"
    })
    mock_openai_client.chat.completions.create.return_value = mock_completion

    # Patch dependencies
    with patch('app.services.content_generator.redis_cache', mock_redis), \
         patch('app.services.content_generator.client', mock_openai_client), \
         patch('app.services.content_generator._initialize_client', return_value=True):

        # Test 1: AI SEO Mode (Schema.org check)
        await create_blog_post(
            text="Test content",
            keywords="test",
            ai_mode="ai_seo",
            input_type="text"
        )
        
        # Verify Redis get called
        mock_redis.get.assert_called()
        
        # Verify Prompt contains AI SEO guidelines
        call_args = mock_openai_client.chat.completions.create.call_args
        prompt_sent = call_args[1]['messages'][1]['content']
        assert "Schema.org" in prompt_sent
        assert "H1, H2, H3" in prompt_sent

        # Test 2: AEO Mode (FAQ check)
        await create_blog_post(
            text="Test content",
            keywords="test",
            ai_mode="aeo",
            input_type="text"
        )
        call_args = mock_openai_client.chat.completions.create.call_args
        prompt_sent = call_args[1]['messages'][1]['content']
        assert "faq-section" in prompt_sent

        # Test 3: GEO Mode (Comparison Table check)
        await create_blog_post(
            text="Test content",
            keywords="test",
            ai_mode="geo",
            input_type="text"
        )
        call_args = mock_openai_client.chat.completions.create.call_args
        prompt_sent = call_args[1]['messages'][1]['content']
        assert "comparison-table" in prompt_sent

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_optimization_integration())
    print("All optimization integration tests passed!")
