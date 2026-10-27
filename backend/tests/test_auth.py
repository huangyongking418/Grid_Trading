import unittest

from app.core.auth import hash_password, verify_password


class PasswordHashTest(unittest.TestCase):
    def test_hash_uses_unique_salt(self):
        first = hash_password("same-password")
        second = hash_password("same-password")

        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("same-password", first))
        self.assertTrue(verify_password("same-password", second))

    def test_rejects_wrong_password(self):
        stored = hash_password("correct-password")

        self.assertFalse(verify_password("wrong-password", stored))

    def test_accepts_legacy_hash(self):
        # 由旧版本固定盐值和 100000 次迭代生成的哈希。
        legacy = (
            "9f10f8a57ed1919a23274fe72b8801f2"
            "055e26669f5ce84224b4e9d76c44e262"
        )

        self.assertTrue(verify_password("legacy-password", legacy))
