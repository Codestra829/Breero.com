class PaymentError(Exception):
    pass


class PaymentNotFound(PaymentError):
    pass


class InvalidPaymentState(PaymentError):
    pass


class IdempotencyConflict(PaymentError):
    pass


class InvalidWebhook(PaymentError):
    pass
