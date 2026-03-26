"""HR Payroll Tools — Attendance, salary calculation, tax filing."""

from titan.capability.mcp.decorator import tool
from titan.core.trust.model import TrustLevel


@tool(
    name="attendance.query",
    description="查询考勤记录：出勤天数、迟到、早退、请假、加班明细",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_attendance(employee_id: str = "", month: str = "2026-03") -> dict:
    """Query attendance records."""
    return {"month": month, "workdays": 22, "attended": 21, "late": 1, "leave": 1,
            "overtime_hours": 12, "leave_type": "年假1天"}


@tool(
    name="salary.calculate",
    description="自动算薪：基本工资+绩效+加班-五险一金-个税-专项附加扣除",
    category="decision",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def calculate_salary(employee_id: str = "", month: str = "2026-03") -> dict:
    """Calculate salary with full breakdown."""
    return {
        "employee": "张三", "month": month,
        "gross": 40000,
        "deductions": {"pension": 3200, "medical": 800, "unemployment": 200,
                      "housing_fund": 4800, "tax": 2891, "special_deduction": 2000},
        "net": 26109,
        "overtime_pay": 2400, "bonus": 0
    }


@tool(
    name="salary.query",
    description="查询薪资明细：工资条、历史薪资、薪资变动记录",
    category="perception",
    trust_level=TrustLevel.AUTONOMOUS,
)
async def query_salary(employee_id: str = "", month: str = "") -> dict:
    """Query salary details."""
    return {"employee": "李四", "position": "前端工程师", "base": 25000,
            "net_last_month": 18650, "ytd_income": 225600, "ytd_tax": 28920}


@tool(
    name="salary.submit",
    description="提交发薪：生成银行发薪文件，对接银行批量代发",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def submit_payroll(month: str = "2026-03") -> dict:
    """Submit payroll for bank processing."""
    return {"month": month, "total_employees": 358, "total_amount": 8562000,
            "bank_file_generated": True, "status": "pending_approval"}


@tool(
    name="tax.declare",
    description="个税申报：自动计算应纳税额，对接税务局系统申报",
    category="execution",
    trust_level=TrustLevel.APPROVE_BEFORE,
)
async def declare_tax(month: str = "2026-03") -> dict:
    """File individual income tax declaration."""
    return {"month": month, "total_employees": 358, "total_tax": 892000,
            "status": "ready_to_submit", "deadline": "2026-04-15"}
