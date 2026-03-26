"""HR Training & Performance Tools."""

from titan.capability.mcp.decorator import tool
from titan.core.trust.model import TrustLevel


@tool(
    name="training.query",
    description="查询培训记录：已完成课程、进行中课程、证书",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_training(employee_id: str = "") -> dict:
    """Query training records."""
    return {"total_courses": 12, "completed": 8, "in_progress": 2,
            "certificates": ["信息安全意识", "项目管理PMP"], "next_due": "合规培训（4月15日截止）"}


@tool(
    name="performance.query",
    description="查询绩效数据：当前周期评分、历史趋势、排名",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_performance(employee_id: str = "", cycle: str = "2026-Q1") -> dict:
    """Query performance data."""
    return {"cycle": cycle, "total_employees": 358,
            "distribution": {"S": 18, "A": 72, "B+": 143, "B": 89, "C": 36},
            "avg_score": 82.5, "completion_rate": "92%"}


@tool(
    name="performance.evaluate",
    description="绩效自动评估：综合 OKR 完成度、360 评价、项目贡献",
    category="decision",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def evaluate_performance(employee_id: str = "", cycle: str = "2026-Q1") -> dict:
    """AI-assisted performance evaluation."""
    return {"employee": "张三", "cycle": cycle, "score": 88, "grade": "A",
            "strengths": ["目标达成率高", "跨部门协作好"], "areas": ["文档规范可提升"],
            "recommendation": "建议晋升答辩"}


@tool(
    name="report.generate",
    description="生成 HR 报告：月度人力报告、人才盘点、招聘分析、离职分析",
    category="presentation",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def generate_report(report_type: str = "monthly", params: dict = None) -> dict:
    """Generate HR reports."""
    return {"type": report_type, "generated": True, "pages": 8,
            "highlights": ["本月净增员15人", "离职率2.1%（行业均值5.8%）", "招聘完成率78%"]}
