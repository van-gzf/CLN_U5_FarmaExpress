from dataclasses import dataclass


class CustomerHasDebt(Exception):
    pass


@dataclass
class Order:
    total: float
    vip: bool = False
    status: str = "NEW"
    discount: float = 0.0

    def confirm(self, customer_debt=0):
        self._reject_if_already_confirmed()
        self._validate_total_and_debt(customer_debt)
        self.discount = round(self.total * 0.15, 2) if self.vip else 0.0
        self.status = "CONFIRMED"
        return self.total - self.discount

    def _reject_if_already_confirmed(self):
        if self.status == "CONFIRMED":
            raise ValueError("already confirmed")

    def _validate_total_and_debt(self, customer_debt):
        if self.total <= 0:
            raise ValueError("total must be positive")
        if customer_debt > 0:
            raise CustomerHasDebt("outstanding debt")
