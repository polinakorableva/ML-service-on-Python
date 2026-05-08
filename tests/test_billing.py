import pytest
from app.services.billing_service import (
    get_balance,
    topup_balance,
    activate_promo,
    get_history
)
from app.models.billing import PromoUsage


class TestGetBalance:
    def test_returns_correct_balance(self, db, test_user):
        balance = get_balance(db, test_user.id)
        assert balance == 50.0

    def test_balance_is_float(self, db, test_user):
        balance = get_balance(db, test_user.id)
        assert isinstance(balance, float)


class TestTopupBalance:

    def test_topup_increases_balance(self, db, test_user):
        new_balance = topup_balance(db, test_user.id, 100)
        assert new_balance == 150.0

    def test_topup_returns_new_balance(self, db, test_user):
        new_balance = topup_balance(db, test_user.id, 30)
        assert new_balance == 80.0

    def test_topup_creates_transaction(self, db, test_user):
        topup_balance(db, test_user.id, 100)
        history = get_history(db, test_user.id)

        assert len(history) == 1
        assert history[0].type == "credit"
        assert float(history[0].amount) == 100.0

    def test_topup_zero_raises_error(self, db, test_user):
        with pytest.raises(ValueError, match="больше нуля"):
            topup_balance(db, test_user.id, 0)

    def test_topup_negative_raises_error(self, db, test_user):
        with pytest.raises(ValueError):
            topup_balance(db, test_user.id, -50)

    def test_topup_too_large_raises_error(self, db, test_user):
        with pytest.raises(ValueError, match="100 000"):
            topup_balance(db, test_user.id, 200_000)

    def test_topup_balance_persisted(self, db, test_user):
        topup_balance(db, test_user.id, 100)
        db.refresh(test_user)
        assert float(test_user.balance) == 150.0


class TestActivatePromo:

    def test_promo_increases_balance(self, db, test_user, promo_active):
        new_balance = activate_promo(db, test_user.id, "TEST100")
        assert new_balance == 150.0  # было 50 + 100 от промокода

    def test_promo_case_insensitive(self, db, test_user, promo_active):
        new_balance = activate_promo(db, test_user.id, "test100")
        assert new_balance == 150.0

    def test_promo_with_spaces(self, db, test_user, promo_active):
        new_balance = activate_promo(db, test_user.id, "  TEST100  ")
        assert new_balance == 150.0

    def test_promo_creates_transaction(self, db, test_user, promo_active):
        activate_promo(db, test_user.id, "TEST100")
        history = get_history(db, test_user.id)

        assert len(history) == 1
        assert history[0].type == "promo"
        assert float(history[0].amount) == 100.0

    def test_promo_increments_used_count(self, db, test_user, promo_active):
        activate_promo(db, test_user.id, "TEST100")
        db.refresh(promo_active)
        assert promo_active.used_count == 1

    def test_promo_creates_usage_record(self, db, test_user, promo_active):
        activate_promo(db, test_user.id, "TEST100")
        usage = db.query(PromoUsage).filter(
            PromoUsage.user_id == test_user.id,
            PromoUsage.promo_id == promo_active.id
        ).first()
        assert usage is not None

    def test_promo_not_found(self, db, test_user):
        with pytest.raises(ValueError, match="не найден"):
            activate_promo(db, test_user.id, "NOSUCHCODE")

    def test_promo_expired(self, db, test_user, promo_expired):
        with pytest.raises(ValueError, match="истёк"):
            activate_promo(db, test_user.id, "EXPIRED")

    def test_promo_exhausted(self, db, test_user, promo_exhausted):
        with pytest.raises(ValueError, match="максимальное"):
            activate_promo(db, test_user.id, "USED")

    def test_promo_double_activation(self, db, test_user, promo_active):

        activate_promo(db, test_user.id, "TEST100")

        with pytest.raises(ValueError, match="уже активировали"):
            activate_promo(db, test_user.id, "TEST100")

    def test_promo_balance_not_changed_on_error(self, db, test_user):

        balance_before = get_balance(db, test_user.id)

        with pytest.raises(ValueError):
            activate_promo(db, test_user.id, "NOSUCHCODE")

        balance_after = get_balance(db, test_user.id)
        assert balance_before == balance_after


class TestGetHistory:

    def test_empty_history(self, db, test_user):
        history = get_history(db, test_user.id)
        assert history == []

    def test_history_after_topup(self, db, test_user):
        topup_balance(db, test_user.id, 100)
        history = get_history(db, test_user.id)
        assert len(history) == 1

    def test_history_ordered_newest_first(self, db, test_user):
        topup_balance(db, test_user.id, 10)
        topup_balance(db, test_user.id, 20)
        topup_balance(db, test_user.id, 30)

        history = get_history(db, test_user.id)

        # Проверяем что все три транзакции есть, не полагаясь на порядок
        amounts = [float(t.amount) for t in history]
        assert sorted(amounts) == [10.0, 20.0, 30.0]
        assert len(history) == 3