"""HR Recruitment Tools — Resume screening, interview scheduling, offer management."""

from titan.capability.mcp.decorator import tool
from titan.core.trust.model import TrustLevel


@tool(
    name="resume.search",
    description="从招聘平台搜索简历（BOSS/猎聘/智联/内推），支持按关键词、经验、学历筛选",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def search_resumes(platform: str = "all", keywords: str = "", min_experience: int = 0) -> dict:
    """Search resumes from recruitment platforms."""
    # Mock implementation
    return {
        "total": 156,
        "matched": 23,
        "top_candidates": [
            {"name": "王小明", "experience": "5年", "education": "985硕士", "score": 92},
            {"name": "李芳", "experience": "3年", "education": "211本科", "score": 87},
            {"name": "陈志强", "experience": "7年", "education": "海归硕士", "score": 85},
        ]
    }


@tool(
    name="resume.parse",
    description="解析简历详情：学历、工作经历、技能栈、期望薪资、稳定性评估",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def parse_resume(resume_id: str) -> dict:
    """Parse resume details."""
    return {
        "name": "王小明", "age": 28, "education": "北京大学 计算机硕士",
        "experience_years": 5, "current_company": "字节跳动",
        "skills": ["Python", "产品设计", "数据分析", "项目管理"],
        "expected_salary": "35-45K", "stability_score": 78,
        "highlight": "有从0到1产品经验，带过5人团队"
    }


@tool(
    name="resume.screen",
    description="AI 智能筛选简历：匹配岗位 JD，综合打分排序，标注亮点和风险",
    category="decision",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def screen_resumes(job_id: str, resume_ids: list = None) -> dict:
    """AI-powered resume screening."""
    return {
        "job": "高级产品经理",
        "screened": 23, "passed": 8, "rejected": 15,
        "top_3": [
            {"name": "王小明", "score": 92, "highlight": "985+大厂+带团队", "risk": "薪资偏高"},
            {"name": "李芳", "score": 87, "highlight": "同行业经验丰富", "risk": "无"},
            {"name": "陈志强", "score": 85, "highlight": "海归+技术背景", "risk": "频繁跳槽"},
        ]
    }


@tool(
    name="interview.schedule",
    description="安排面试：自动协调候选人和面试官时间，发送面试邀约和提醒",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def schedule_interview(candidate_id: str, interviewer_id: str, time: str = "") -> dict:
    """Schedule interview with automatic calendar coordination."""
    return {"status": "scheduled", "candidate": "王小明", "interviewer": "张总监",
            "time": "2026-03-28 14:00", "location": "会议室A3", "notification_sent": True}


@tool(
    name="offer.send",
    description="发送 Offer：生成 Offer Letter，包含薪资包、福利、入职日期",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def send_offer(candidate_id: str, base_salary: int = 0, start_date: str = "") -> dict:
    """Generate and send offer letter."""
    return {"status": "sent", "candidate": "王小明", "position": "高级产品经理",
            "package": {"base": "40K/月", "bonus": "3个月", "stock": "期权5万股"},
            "start_date": "2026-04-01", "deadline": "2026-03-30"}
