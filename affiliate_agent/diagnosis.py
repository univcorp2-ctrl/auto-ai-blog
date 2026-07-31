from __future__ import annotations

from affiliate_agent.models import DiagnosisInput, DiagnosisResult


def diagnose_costs(data: DiagnosisInput) -> DiagnosisResult:
    if data.mobile_lines < 1 or data.household_size < 1:
        raise ValueError("mobile_lines and household_size must be at least 1")
    if min(data.mobile_monthly_yen, data.internet_monthly_yen, data.electricity_monthly_yen) < 0:
        raise ValueError("monthly costs must be non-negative")

    categories: list[str] = []
    notes: list[str] = []
    low = 0
    high = 0

    mobile_per_line = data.mobile_monthly_yen / data.mobile_lines
    if mobile_per_line >= 4_500:
        categories.append("mobile")
        mobile_gap = max(0, data.mobile_monthly_yen - data.mobile_lines * 3_500)
        low += round(mobile_gap * 0.25)
        high += round(mobile_gap * 0.7)
        notes.append("1回線あたりの通信費が高めです。容量、通話、端末残債を分けて比較してください。")

    if data.internet_monthly_yen >= 5_500 or data.internet_type in {"unknown", "legacy", "home-router"}:
        categories.append("internet")
        internet_gap = max(500, data.internet_monthly_yen - 4_500)
        low += round(internet_gap * 0.3)
        high += round(internet_gap * 0.8)
        notes.append("回線速度だけでなく、工事費残債、解約金、セット割の消失を含めて確認してください。")

    electricity_baseline = 7_000 + max(0, data.household_size - 1) * 2_000
    if data.electricity_monthly_yen >= electricity_baseline * 1.15:
        categories.append("electricity")
        electricity_gap = max(500, data.electricity_monthly_yen - electricity_baseline)
        low += round(electricity_gap * 0.1)
        high += round(electricity_gap * 0.35)
        notes.append("電力は地域、使用量、燃料費調整、解約条件を同じ期間で比較してください。")

    if not categories:
        categories.append("general_review")
        notes.append("大きな割高サインはありません。更新月とセット割だけ定期確認してください。")

    if not data.willing_to_switch:
        notes.append("乗り換え前提ではなく、現契約のプラン変更や不要オプション解約から確認します。")

    return DiagnosisResult(
        categories=tuple(categories),
        monthly_saving_low_yen=max(0, low),
        monthly_saving_high_yen=max(low, high),
        notes=tuple(notes),
    )
