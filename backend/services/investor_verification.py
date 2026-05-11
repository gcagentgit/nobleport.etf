from backend.models.investor import InvestorStatus

ALLOWED_TRANSITIONS: dict[InvestorStatus, set[InvestorStatus]] = {
    InvestorStatus.PENDING: {InvestorStatus.DOCS_REQUESTED, InvestorStatus.REJECTED},
    InvestorStatus.DOCS_REQUESTED: {InvestorStatus.UNDER_REVIEW, InvestorStatus.REJECTED},
    InvestorStatus.UNDER_REVIEW: {InvestorStatus.VERIFIED, InvestorStatus.REJECTED},
    InvestorStatus.VERIFIED: {InvestorStatus.EXPIRED},
    InvestorStatus.REJECTED: set(),
    InvestorStatus.EXPIRED: {InvestorStatus.PENDING},
}


class InvalidTransitionError(Exception):
    def __init__(self, current: InvestorStatus, target: InvestorStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from {current.value} to {target.value}")


def validate_transition(current: InvestorStatus, target: InvestorStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(current, target)
