"""HR Employee Tools — Query, transfer, offboarding, benefits."""

from titan.capability.mcp.decorator import tool
from titan.core.trust.model import TrustLevel


@tool(
    name="employee.query",
    description="查询员工信息：姓名、部门、岗位、入职日期、合同状态",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_employee(name: str = "", dept: str = "", status: str = "active") -> dict:
    """Query employee information."""
    return {
        "total_active": 358, "total_probation": 23, "total_contract_expiring_30d": 5,
        "departments": [
            {"name": "产品部", "headcount": 45},
            {"name": "技术部", "headcount": 128},
            {"name": "市场部", "headcount": 56},
            {"name": "运营部", "headcount": 67},
            {"name": "HR/行政", "headcount": 32},
            {"name": "财务部", "headcount": 30},
        ]
    }


@tool(
    name="benefit.query",
    description="查询福利信息：社保基数、公积金、年假余额、补充医疗",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_benefits(employee_id: str = "", benefit_type: str = "all") -> dict:
    """Query employee benefits."""
    return {
        "employee": "李四",
        "social_insurance": {"base": 28000, "pension": 2240, "medical": 560},
        "housing_fund": {"base": 28000, "monthly": 3360},
        "annual_leave": {"total": 10, "used": 3, "remaining": 7},
        "supplementary_medical": "已开通", "gym_membership": "已开通"
    }


@tool(
    name="org.chart",
    description="查询组织架构：部门层级、人员分布、汇报关系",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_org_chart(dept: str = "") -> dict:
    """Query organization chart."""
    return {
        "company": "示例科技有限公司", "total_employees": 358,
        "departments": [
            {"name": "产品部", "head": "王总监", "headcount": 45, "sub_teams": ["产品策划", "用户研究", "项目管理"]},
            {"name": "技术部", "head": "李CTO", "headcount": 128, "sub_teams": ["前端", "后端", "算法", "基础设施", "测试"]},
            {"name": "市场部", "head": "赵VP", "headcount": 56, "sub_teams": ["品牌", "增长", "内容"]},
        ]
    }


@tool(
    name="transfer.initiate",
    description="发起调岗/调级：自动走审批流程、同步薪酬变更、更新组织架构",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def initiate_transfer(employee_id: str, new_dept: str = "", new_position: str = "", new_level: str = "") -> dict:
    """Initiate employee transfer."""
    return {"employee": "赵六", "from": "技术部-后端工程师", "to": f"{new_dept}-{new_position}",
            "salary_change": "+15%", "status": "pending_approval"}


@tool(
    name="offboard.initiate",
    description="发起离职流程：交接清单、资产回收、权限注销、离职面谈",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def initiate_offboarding(employee_id: str, reason: str = "", last_day: str = "") -> dict:
    """Initiate offboarding workflow."""
    return {
        "employee": "钱七", "reason": reason, "last_day": last_day,
        "checklist": [
            {"item": "工作交接", "assignee": "直属上级", "status": "pending"},
            {"item": "资产回收（电脑/工牌）", "assignee": "IT部", "status": "pending"},
            {"item": "权限注销", "assignee": "IT部", "status": "pending"},
            {"item": "社保停缴", "assignee": "HR", "status": "pending"},
            {"item": "离职面谈", "assignee": "HRBP", "status": "pending"},
            {"item": "离职证明", "assignee": "HR", "status": "pending"},
        ]
    }


@tool(
    name="risk.assess",
    description="员工风险评估：离职倾向分析、合同到期预警、绩效异常检测",
    category="decision",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def assess_risk(employee_id: str = "") -> dict:
    """Assess employee risk factors."""
    return {
        "high_risk_count": 3,
        "risks": [
            {"employee": "孙八", "type": "离职倾向", "score": 85, "signals": ["近期频繁请假", "更新了简历"]},
            {"employee": "周九", "type": "合同到期", "days_remaining": 15, "action": "需发起续签"},
            {"employee": "吴十", "type": "绩效异常", "detail": "连续2个周期绩效C"},
        ]
    }
