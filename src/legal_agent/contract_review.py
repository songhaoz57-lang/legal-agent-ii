# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from dataclasses import dataclass, field

RISK_HIGH = 'high'
RISK_MEDIUM = 'medium'
RISK_LOW = 'low'


@dataclass
class ClauseRisk:
    clause_type: str
    risk_level: str
    pattern: str
    found_text: str
    suggestion: str


@dataclass
class ContractReviewResult:
    risks: list = field(default_factory=list)
    missing_clauses: list = field(default_factory=list)
    overall_score: int = 100



RISK_PATTERNS = [
    ClauseRisk(
        clause_type='违约金过高',
        risk_level=RISK_HIGH,
        pattern='(?:违约金|违约).{0,30}[3-9]\d%|(?:合同|总价|金额).{0,10}[3-9]\d%.{0,30}(?:违约金|违约)',
        found_text='',
        suggestion='违约金超过实际损失30%可被法院调减(民法典第585条)。建议改为以实际损失为限，上限不超过合同总价的20%。',
    ),
    ClauseRisk(
        clause_type='单方解除权不对等',
        risk_level=RISK_HIGH,
        pattern='(?:甲方|卖方|出租方|许可方|委托方|服务方).{0,20}(?:有权|可以|有权利).{0,30}(?:单方|随时|任意|无须|无需|即可).{0,20}(?:解除|终止|撤销)',
        found_text='',
        suggestion='单方解除权不对等可能被认定为格式条款无效(民法典第497条)。建议双方解除权对等，或限定在严重违约情形下。',
    ),
    ClauseRisk(
        clause_type='无限责任条款',
        risk_level=RISK_HIGH,
        pattern='(?:无限|全部|一切|所有|任何).{0,20}(?:责任|赔偿|损失|损害).{0,30}(?:承担|负责|赔偿|补偿)',
        found_text='',
        suggestion='无限责任条款风险极高。建议设置责任上限(如合同金额的1-3倍)，明确排除间接损失和利润损失。',
    ),
    ClauseRisk(
        clause_type='管辖地不利',
        risk_level=RISK_HIGH,
        pattern='(?:争议|纠纷|诉讼|起诉).{0,30}(?:由|在|向).{0,10}(?:乙方|对方|买方|承租方|受托方|被许可方|卖方|出租方).{0,20}(?:所在地|法院|仲裁)',
        found_text='',
        suggestion='管辖地在对方所在地增加维权成本。建议约定已方所在地法院管辖或选择仲裁。',
    ),
    ClauseRisk(
        clause_type='全部风险转嫁',
        risk_level=RISK_HIGH,
        pattern='(?:所有|全部|一切|任何).{0,20}(?:风险|损失|责任|后果).{0,20}(?:由|归|自行|独立).{0,15}(?:承担|负责|处理)',
        found_text='',
        suggestion='全部风险由一方承担可能显失公平(民法典第151条)。建议按过错程度合理分担风险。',
    ),
    ClauseRisk(
        clause_type='保密期限不合理',
        risk_level=RISK_MEDIUM,
        pattern='(?:保密|机密|商业秘密).{0,30}(?:永久|无限期|永远|终身)',
        found_text='',
        suggestion='永久保密条款可能被认定不合理。建议保密期限为合同终止后2-5年，商业秘密可长期但需明确范围。',
    ),
    ClauseRisk(
        clause_type='竞业限制过宽',
        risk_level=RISK_MEDIUM,
        pattern='(?:竞业|不竞争|竞业禁止).{0,30}(?:所有|任何|全部|一切).{0,20}(?:行业|领域|业务|市场)',
        found_text='',
        suggestion='竞业限制范围过宽可能被认定无效。建议限缩为与公司有直接竞争关系的特定业务领域和地域，期限不超过2年。',
    ),
    ClauseRisk(
        clause_type='验收标准模糊',
        risk_level=RISK_MEDIUM,
        pattern='(?:验收|确认|认可|合格).{0,30}(?:由.{0,10}自行|单方.{0,10}决定|任意|随时|自行判断)',
        found_text='',
        suggestion='验收标准由一方单方决定可能导致争议。建议约定客观可量化的验收标准和第三方检测机制。',
    ),
    ClauseRisk(
        clause_type='知识产权归属不清',
        risk_level=RISK_MEDIUM,
        pattern='(?:知识产权|著作权|专利|技术成果|商标).{0,30}(?:归.{0,10}所有|属于.{0,10}所有|归.{0,10}独占)',
        found_text='',
        suggestion='请明确约定知识产权归属(委托方/受托方/共有)，以及后续使用、许可、转让的权利分配。',
    ),
    ClauseRisk(
        clause_type='付款节点不明确',
        risk_level=RISK_MEDIUM,
        pattern='(?:条件成就|满足要求|待确认|待通知).{0,20}(?:付款|支付|结算)|(?:付款|支付|结算).{0,30}(?:条件成就|满足要求|待确认|待通知)',
        found_text='',
        suggestion='付款条件过于模糊。建议约定具体可核实或可验证的里程碑节点，如“验收合格后X个工作日内”。',
    ),
    ClauseRisk(
        clause_type='不可抗力定义过窄',
        risk_level=RISK_LOW,
        pattern='不可抗力.{0,40}(?:仅限|仅包括|只包括|(?<!包括但不)限于)(?!.{0,10}但不).{0,20}(?:自然灾害|战争|地震|洪水)',
        found_text='',
        suggestion='不可抗力定义过窄。建议采用概括+列举方式，包含流行病、政府行为、社会异常事件等。',
    ),
    ClauseRisk(
        clause_type='自动续约条款',
        risk_level=RISK_LOW,
        pattern='(?:合同|协议|本协议|本合同).{0,30}(?:自动.{0,10}续约|自动.{0,10}延长|自动.{0,10}延期|默认.{0,10}续约)',
        found_text='',
        suggestion='自动续约可能导致被动绑定。建议改为到期前X日书面确认是否续约。',
    ),
    ClauseRisk(
        clause_type='免责条款过宽',
        risk_level=RISK_LOW,
        pattern='(?:不.{0,10}(?:承担|负责|赔偿)|免.{0,10}(?:责|除)).{0,20}(?:任何|一切|所有|全部).{0,20}(?:责任|损失|损害)',
        found_text='',
        suggestion='过宽的免责条款可能被认定为无效(民法典第506条)。',
    ),
]


EXPECTED_CLAUSES = [
    ('违约责任', '违约|违约责任|赔偿|违约金'),
    ('争议解决', '争议|纠纷|仲裁|诉讼|管辖'),
    ('保密条款', '保密|机密|秘密|不披露'),
    ('知识产权', '知识产权|著作权|专利|商标|技术成果'),
    ('不可抗力', '不可抗力|意外事件|情势变更'),
    ('合同期限', '期限|有效期|起止|终止'),
    ('付款条款', '付款|支付|价款|费用|报酬'),
    ('交付验收', '交付|验收|完成|移交'),
    ('合同解除', '解除|终止|撤销'),
    ('通知送达', '通知|送达|地址|联系方式'),
]
def review_contract(text: str) -> ContractReviewResult:
    result = ContractReviewResult()

    for risk in RISK_PATTERNS:
        matches = re.findall(risk.pattern, text, re.IGNORECASE)
        if matches:
            r = ClauseRisk(
                clause_type=risk.clause_type,
                risk_level=risk.risk_level,
                pattern=risk.pattern,
                found_text=str(matches[0])[:120],
                suggestion=risk.suggestion,
            )
            result.risks.append(r)
            if risk.risk_level == RISK_HIGH:
                result.overall_score -= 15
            elif risk.risk_level == RISK_MEDIUM:
                result.overall_score -= 8
            else:
                result.overall_score -= 3

    result.overall_score = max(0, result.overall_score)

    for clause_name, pattern in EXPECTED_CLAUSES:
        if not re.search(pattern, text, re.IGNORECASE):
            result.missing_clauses.append(clause_name)
            result.overall_score -= 5

    result.overall_score = max(0, result.overall_score)
    return result


def format_review(result: ContractReviewResult) -> str:
    lines = ['# 合同审查报告', '']

    if result.overall_score >= 80:
        level = '良好'
    elif result.overall_score >= 60:
        level = '一般 - 需关注'
    else:
        level = '高风险 - 强烈建议律师审查'
    lines.append('**综合评分: {}/100** ({})'.format(result.overall_score, level))
    lines.append('')

    if result.risks:
        lines.append('## 发现的风险条款 ({})'.format(len(result.risks)))
        lines.append('')
        for r in result.risks:
            icon_map = {RISK_HIGH: '🔴 高风险', RISK_MEDIUM: '🟠 中风险', RISK_LOW: '🔵 低风险'}
            icon = icon_map.get(r.risk_level, '?')
            lines.append('### {}: {}'.format(icon, r.clause_type))
            lines.append('- 发现文本: “{}”'.format(r.found_text[:120]))
            lines.append('- 建议: {}'.format(r.suggestion))
            lines.append('')
    else:
        lines.append('## 未检测到明显风险条款')
        lines.append('')

    if result.missing_clauses:
        lines.append('## 缺失 / 不明确的条款 ({})'.format(len(result.missing_clauses)))
        lines.append('以下标准条款未被检测到:')
        for c in result.missing_clauses:
            lines.append('- {}'.format(c))
        lines.append('')

    lines.append('---')
    lines.append('*自动化审查仅供参考，不构成法律意见。请委托执业律师对最终合同进行审查。*')
    return '\n'.join(lines)
