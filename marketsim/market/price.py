from decimal import Decimal, ROUND_HALF_UP

class Price(Decimal):
    TICK_SIZE = Decimal("0.01")

    def __new__(cls, value : Decimal|float|int):

        d = Decimal(str(value))
        if not d.is_finite():
            raise ValueError("Price must be finite")
        return super().__new__(
            cls,
            d.quantize(cls.TICK_SIZE, rounding=ROUND_HALF_UP)
        )
