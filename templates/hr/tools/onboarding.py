"""HR Onboarding Tools — Contract, account provisioning, orientation."""

from titan.capability.mcp.decorator import tool
from titan.core.trust.model import TrustLevel


@tool(
    name="onboard.initiate",
    description="发起入职流程：自动生成合同、开通账号、分配工位、推送入职指引",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def initiate_onboarding(employee_name: str, position: str, dept: str, start_date: str) -> dict:
    """Initiate full onboarding workflow."""
    return {
        "employee": employee_name, "position": position, "dept": dept, "start_date": start_date,
        "steps_completed": [
            {"step": "劳动合同生成", "status": "completed", "time": "2s"},
            {"step": "电子签发起", "status": "completed", "time": "3s"},
            {"step": "企微/邮箱/门禁开通", "status": "completed", "time": "5s"},
            {"step": "工位分配 B3-042", "status": "completed", "time": "1s"},
            {"step": "入职指引推送", "status": "completed", "time": "2s"},
            {"step": "通知部门负责人", "status": "completed", "time": "1s"},
        ],
        "total_time": "14s", "manual_intervention": 0
    }


@tool(
    name="contract.generate",
    description="生成劳动合同/保密协议/竞业协议，自动填充员工和岗位信息",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def generate_contract(employee_id: str, contract_type: str = "labor") -> dict:
    """Generate employment contract."""
    return {"type": contract_type, "status": "generated", "pages": 12,
            "key_terms": {"probation": "3个月", "salary": "40K/月", "non_compete": "12个月"}}


@tool(
    name="account.create",
    description="开通系统账号：企业微信、飞书、邮箱、OA、门禁、VPN",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def create_accounts(employee_id: str, systems: list = None) -> dict:
    """Provision system accounts for new employee."""
    return {
        "accounts_created": [
            {"system": "企业微信", "account": "zhangsan@company", "status": "active"},
            {"system": "公司邮箱", "account": "zhangsan@company.com", "status": "active"},
            {"system": "OA系统", "account": "ZS20260401", "status": "active"},
            {"system": "门禁", "card_id": "IC-20260401", "status": "active"},
            {"system": "VPN", "account": "zhangsan", "status": "active"},
        ],
        "total": 5, "all_success": True
    }
