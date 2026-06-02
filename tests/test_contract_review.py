# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest
from legal_agent.contract_review import (
    review_contract, format_review,
    RISK_HIGH, RISK_MEDIUM, RISK_LOW,
    ContractReviewResult, ClauseRisk,
)


class TestReviewContract:

    def test_empty_contract(self):
        result = review_contract('')
        assert isinstance(result, ContractReviewResult)

    def test_clean_contract_scores_high(self):
        text = '违约责任：任何一方违反本合同约定，应向守约方支付违约金，违约金不超过实际损失的20%。\n争议解决：因本合同产生的争议，双方应友好协商；协商不成的，提交北京仲裁委员会仲裁。\n保密：双方对合同内容承担保密义务，保密期限为合同终止后3年。\n知识产权：委托开发产生的知识产权由双方共有。\n不可抗力：因不可抗力导致无法履行的，受影响方应及时通知对方，不可抗力包括但不限于自然灾害、战争、疫情、政府行为等。\n合同期限：本合同有效期自签署之日起至2027年12月31日止。\n付款：甲方应于验收合格后10个工作日内支付全部款项。\n交付验收：乙方应于2026年6月30日前完成交付，甲方应在收到货物后5个工作日内完成验收。\n合同解除：任何一方严重违约的，守约方有权书面通知解除合同。\n通知送达：双方往来通知应以书面形式送达以下地址。'
        result = review_contract(text)
        assert result.overall_score >= 80
        assert len(result.risks) == 0

    def test_high_penalty_detected(self):
        text = '违约金为合同总金额的50%，违约方应支付。'
        result = review_contract(text)
        risks = [r for r in result.risks if '\u8fdd\u7ea6\u91d1' in r.clause_type]
        assert len(risks) >= 1
        assert risks[0].risk_level == RISK_HIGH

    def test_unilateral_termination_detected(self):
        text = '甲方有权随时单方解除本合同，无须任何理由。'
        result = review_contract(text)
        risks = [r for r in result.risks if '\u89e3\u9664' in r.clause_type]
        assert len(risks) >= 1
        assert risks[0].risk_level == RISK_HIGH

    def test_unlimited_liability_detected(self):
        text = '乙方对因本合同产生的任何及所有损失承担全部赔偿责任。'
        result = review_contract(text)
        risks = [r for r in result.risks if '\u8d23\u4efb' in r.clause_type]
        assert len(risks) >= 1

    def test_unfavorable_jurisdiction_detected(self):
        text = '因本合同产生的争议，均由乙方所在地法院管辖。'
        result = review_contract(text)
        risks = [r for r in result.risks if '\u7ba1\u8f96' in r.clause_type]
        assert len(risks) >= 1
        assert risks[0].risk_level == RISK_HIGH

    def test_perpetual_confidentiality_detected(self):
        text = '乙方对保密信息承担永久保密义务。'
        result = review_contract(text)
        risks = [r for r in result.risks if '\u4fdd\u5bc6' in r.clause_type]
        assert len(risks) >= 1

    def test_vague_payment_terms_detected(self):
        text = '甲方应在条件成就后支付服务费用。'
        result = review_contract(text)
        risks = [r for r in result.risks if '\u4ed8\u6b3e' in r.clause_type]
        assert len(risks) >= 1

    def test_missing_clauses_detected(self):
        text = '双方约定：甲方卖给乙方一批货，价格100元。'
        result = review_contract(text)
        assert len(result.missing_clauses) > 5

    def test_score_capped_at_zero(self):
        text = '违约金100% 争议由对方法院管辖 承担一切责任 全部风险自担 永久保密 竞业限制所有行业'
        result = review_contract(text)
        assert result.overall_score >= 0

    def test_found_text_captured(self):
        text = '违约金为合同总价50%。'
        result = review_contract(text)
        assert len(result.risks) > 0
        assert len(result.risks[0].found_text) > 0


class TestFormatReview:

    def test_format_includes_score(self):
        result = review_contract('普通买卖合同，双方友好协商。')
        report = format_review(result)
        assert '评分' in report or 'Score' in report or '/100' in report

    def test_format_notes_risks(self):
        result = review_contract('违约金为合同金额的80%')
        report = format_review(result)
        assert len(report) > 0

    def test_format_notes_missing(self):
        result = review_contract('简单协议，内容很少。')
        report = format_review(result)
        assert '缺失' in report or 'Missing' in report

    def test_format_includes_disclaimer(self):
        result = review_contract('test')
        report = format_review(result)
        assert '仅供参考' in report or 'reference' in report.lower()


class TestScoringConsistency:

    def test_score_decreases_with_more_risks(self):
        clean = '双方约定价格100元，合同期限1年，付款在交货后3日。'
        risky = '违约金80% 对方管辖 永久保密 无限责任 全部风险自行承担'
        clean_result = review_contract(clean)
        risky_result = review_contract(risky)
        assert risky_result.overall_score < clean_result.overall_score