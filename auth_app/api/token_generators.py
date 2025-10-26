from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    # Basis: User-ID + timestamp + is_active

    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)


class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    # Basis: User-ID + Passwort-Hash + timestamp

    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(user.password) + str(timestamp)
