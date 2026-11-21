"""Issue #30。時刻を戻すとき、前後の独立した追記を消さない。"""
import unittest

from test_redacted_insertion import revert


class AddedSentenceTests(unittest.TestCase):
    def test_requested_sentence_after_correction(self):
        actual, _ = revert("受付は15時です。", "受付は16時です。受付は予約制です。",
                           "「受付は予約制です。」を追記してください。")
        self.assertEqual(actual, "受付は15時です。受付は予約制です。")

    def test_paraphrased_request_before_correction(self):
        actual, _ = revert("受付は15時に開始します。", "受付は予約制です。受付は16時に開始します。",
                           "受付が予約制であることもお知らせください。")
        self.assertEqual(actual, "受付は予約制です。受付は15時に開始します。")

    def test_added_fact_in_split_sentence(self):
        actual, _ = revert("受付は15時で、予約が必要です。", "受付は16時です。予約には会員証が必要です。",
                           "予約に会員証が必要なことを追記してください。")
        self.assertIn("15時", actual)
        self.assertIn("予約には会員証が必要です。", actual)


if __name__ == "__main__":
    unittest.main()
