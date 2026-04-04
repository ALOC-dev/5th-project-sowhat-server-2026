class UserNotFoundError(Exception):
    def __init__(self):
        self.message = "사용자를 찾을 수 없습니다."


class ArticleNotFoundError(Exception):
    def __init__(self):
        super().__init__("기사를 찾을 수 없습니다.")


# 분석결과 없을 때 임시로 에러처리
class AnalysisNotFoundError(Exception):
    def __init__(self):
        super().__init__("분석 결과를 찾을 수 없습니다.")
