import pytest
from unittest.mock import patch, Mock
from app.services.crawler import get_text_from_url

@pytest.mark.asyncio
async def test_get_text_from_url_success():
    """성공적인 URL 크롤링 테스트"""
    mock_response = Mock()
    mock_response.text = """
    <html>
        <body>
            <article>
                <h1>테스트 제목</h1>
                <p>테스트 내용입니다.</p>
                <h2>부제목</h2>
                <p>추가 내용입니다.</p>
            </article>
        </body>
    </html>
    """
    mock_response.raise_for_status.return_value = None
    
    with patch('requests.get', return_value=mock_response):
        result = await get_text_from_url("https://example.com")
        
        assert "테스트 제목" in result
        assert "테스트 내용입니다" in result
        assert "부제목" in result

@pytest.mark.asyncio
async def test_get_text_from_url_http_error():
    """HTTP 오류 테스트"""
    with patch('requests.get', side_effect=Exception("Connection error")):
        result = await get_text_from_url("https://invalid-url.com")
        assert result.startswith("오류:")

@pytest.mark.asyncio
async def test_get_text_from_url_no_content():
    """콘텐츠가 없는 경우 테스트"""
    mock_response = Mock()
    mock_response.text = "<html><body></body></html>"
    mock_response.raise_for_status.return_value = None
    
    with patch('requests.get', return_value=mock_response):
        result = await get_text_from_url("https://empty-content.com")
        assert "본문 내용을 찾을 수 없습니다" in result 