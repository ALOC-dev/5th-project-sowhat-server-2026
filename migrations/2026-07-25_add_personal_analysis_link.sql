-- 개인해설에 조회/신청 링크 컬럼 추가
-- link_name: LLM이 고른 공식 창구 이름 (app/services/llm/reference_links.py의 목록에 있는 값)
-- link: 서버가 link_name을 변환한 실제 주소
--
-- 이 프로젝트에는 마이그레이션 도구가 없어 DB에 직접 실행해야 한다.
ALTER TABLE personal_analysis
    ADD COLUMN IF NOT EXISTS link_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS link VARCHAR(255);
