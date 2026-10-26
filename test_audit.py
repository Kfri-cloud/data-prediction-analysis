"""Adversarial tests of temporal admission, not tests of predictive skill."""
import unittest
from audit_data import check_point_in_time

CUTOFF = "2024-01-31T15:00:00Z"
NEWS = {"published_at": "2024-01-30T10:00:00Z", "available_at": "2024-01-30T10:00:00Z",
        "source_url": "https://example.org/news", "snapshot_sha256": "fixture-only"}


class TemporalGateTests(unittest.TestCase):
    def test_past_document_metadata_passes(self):
        self.assertTrue(check_point_in_time(NEWS, CUTOFF)["eligible"])

    def test_reference_period_is_not_publication_date(self):
        self.assertFalse(check_point_in_time({"start_date": "2020-01-01", "end_date": "2020-01-31", "fact": "text"}, CUTOFF)["eligible"])

    def test_future_publication_rejected(self):
        row = dict(NEWS, published_at="2024-02-01T00:00:00Z", available_at="2024-02-01T00:00:00Z")
        self.assertFalse(check_point_in_time(row, CUTOFF)["eligible"])

    def test_later_article_revision_rejected(self):
        self.assertFalse(check_point_in_time(dict(NEWS, available_at="2024-02-10T00:00:00Z"), CUTOFF)["eligible"])

    def test_timezone_equivalence(self):
        row = dict(NEWS, published_at="2024-02-01T00:00:00+09:00", available_at="2024-02-01T00:00:00+09:00")
        self.assertTrue(check_point_in_time(row, CUTOFF)["eligible"])

    def test_date_without_timezone_rejected(self):
        self.assertFalse(check_point_in_time(dict(NEWS, published_at="2024-01-30"), CUTOFF)["eligible"])

    def test_numeric_revision_without_vintage_rejected(self):
        row = {"released_at": "2024-01-30T10:00:00Z", "available_at": "2024-01-30T10:00:00Z",
               "source_url": "https://example.org/statistics", "snapshot_sha256": "fixture-only"}
        self.assertFalse(check_point_in_time(row, CUTOFF, "numeric")["eligible"])

    def test_numeric_future_release_rejected(self):
        row = {"released_at": "2024-02-02T00:00:00Z", "available_at": "2024-02-02T00:00:00Z",
               "source_url": "https://example.org/statistics", "snapshot_sha256": "fixture-only", "vintage_id": "20240202"}
        self.assertFalse(check_point_in_time(row, CUTOFF, "numeric")["eligible"])

    def test_availability_cannot_precede_publication(self):
        row = dict(NEWS, published_at="2024-01-31T10:00:00Z", available_at="2024-01-30T10:00:00Z")
        self.assertFalse(check_point_in_time(row, CUTOFF)["eligible"])

    def test_missing_timestamp_rejected(self):
        self.assertFalse(check_point_in_time(dict(NEWS, available_at=""), CUTOFF)["eligible"])


if __name__ == "__main__":
    unittest.main()
