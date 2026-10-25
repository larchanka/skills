#!/usr/bin/env python3
"""Unit tests for yt-random-comment-picker."""

import json
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pick_comment


class TestPickComment(unittest.TestCase):
    def setUp(self):
        self.sample_data = {
            "title": "Sample Video",
            "comment_count": 5,
            "comments": [
                {
                    "id": "c1",
                    "author": "Alice",
                    "text": "Great video!\nReally enjoyed it.",
                    "likes": 10,
                },
                {
                    "id": "c2",
                    "author": "Bob",
                    "text": "First comment from Bob",
                    "likes": 2,
                },
                {
                    "id": "c3",
                    "author": "Alice",
                    "text": "Second comment from Alice (duplicate author)",
                    "likes": 0,
                },
                {
                    "id": "c4",
                    "author": "Charlie",
                    "text": "Count me in!",
                    "likes": 5,
                },
                {
                    "id": "c5",
                    "author": "",
                    "text": "Missing author comment",
                    "likes": 1,
                },
            ],
        }

    def test_extract_top_level_comments(self):
        comments = pick_comment.extract_top_level_comments(self.sample_data)
        # Should exclude c5 (missing author)
        self.assertEqual(len(comments), 4)
        authors = [c["author"] for c in comments]
        self.assertEqual(authors, ["Alice", "Bob", "Alice", "Charlie"])

    def test_extract_top_level_comments_empty(self):
        self.assertEqual(pick_comment.extract_top_level_comments({}), [])
        self.assertEqual(pick_comment.extract_top_level_comments({"comments": []}), [])

    def test_filter_unique_authors(self):
        comments = pick_comment.extract_top_level_comments(self.sample_data)
        unique = pick_comment.filter_unique_authors(comments)

        self.assertEqual(len(unique), 3)
        authors = [c["author"] for c in unique]
        self.assertEqual(authors, ["Alice", "Bob", "Charlie"])

        # Check that Alice's FIRST comment was preserved, not the duplicate
        alice_comment = next(c for c in unique if c["author"] == "Alice")
        self.assertIn("Great video!", alice_comment["text"])
        self.assertNotIn("duplicate author", alice_comment["text"])

    def test_select_random_comment(self):
        # Empty list returns None
        self.assertIsNone(pick_comment.select_random_comment([]))

        # Non-empty list selection
        comments = [{"author": "User1", "text": "Hello"}]
        selected = pick_comment.select_random_comment(comments)
        self.assertEqual(selected["author"], "User1")

        # Deterministic selection with fixed seed
        multiple = [
            {"author": "A", "text": "1"},
            {"author": "B", "text": "2"},
            {"author": "C", "text": "3"},
        ]
        random.seed(42)
        choice = pick_comment.select_random_comment(multiple)
        self.assertIn(choice, multiple)

    def test_format_comment(self):
        comment = {
            "author": "TestUser",
            "text": "Line one.\nLine two   with   spaces.\n",
        }
        formatted = pick_comment.format_comment(comment)
        self.assertIn("Author: TestUser", formatted)
        # Cleaned whitespace and newlines
        self.assertIn("Comment: Line one. Line two with spaces.", formatted)

    @patch("subprocess.run")
    def test_download_comments_success(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        dummy_json = {"title": "Mock Video", "comments": [{"author": "Tester", "text": "Cool"}]}

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(dummy_json))):
            data = pick_comment.download_comments("https://youtube.com/watch?v=123", "/tmp/fake.json")
            self.assertIsNotNone(data)
            self.assertEqual(data["title"], "Mock Video")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("yt-dlp", args)
        self.assertIn("--skip-download", args)
        self.assertIn("--write-comments", args)

    @patch("subprocess.run")
    def test_download_comments_failure(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = "Video unavailable"
        mock_run.return_value = mock_proc

        data = pick_comment.download_comments("https://youtube.com/watch?v=invalid", "/tmp/fake.json")
        self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main()
