
# searchengineland.com 사이트용 커스텀 크롤러
def crawl_searchengineland_com(soup):
    """searchengineland.com 사이트 전용 크롤링 함수"""
    main_content = None
    
    # 사이트별 특화 선택자들
    selectors = [
        # 여기에 분석 결과를 바탕으로 한 선택자들을 추가하세요
    ]
    
    for selector in selectors:
        main_content = soup.select_one(selector)
        if main_content:
            logger.info(f"searchengineland.com 사이트 본문을 찾았습니다: {selector}")
            break
    
    if not main_content:
        # 폴백: 일반적인 선택자들
        fallback_selectors = ['article', 'main', '.content', '.post-content']
        for selector in fallback_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
    
    if not main_content:
        main_content = soup.body
    
    return main_content
