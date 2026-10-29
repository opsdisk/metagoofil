import os
import tempfile
import unittest

import metagoofil


class TestGetSafeFileName(unittest.TestCase):
    """Tests for metagoofil.get_safe_file_name."""

    def setUp(self) -> None:
        """Create a temporary save directory for each test.

        Args:
            None

        Returns:
            None
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.save_directory = self.temp_dir.name

    def test_simple_file_name(self) -> None:
        """A plain URL returns the final path component.

        Args:
            None

        Returns:
            None
        """
        result = metagoofil.get_safe_file_name(
            "https://example.com/docs/report.pdf", self.save_directory
        )
        self.assertEqual(result, "report.pdf")

    def test_query_string_and_fragment_removed(self) -> None:
        """Query strings and fragments are not part of the file name.

        Args:
            None

        Returns:
            None
        """
        result = metagoofil.get_safe_file_name(
            "https://example.com/report.pdf?a=1#frag", self.save_directory
        )
        self.assertEqual(result, "report.pdf")

    def test_percent_encoded_space_decoded(self) -> None:
        """Percent-encoded characters are decoded.

        Args:
            None

        Returns:
            None
        """
        result = metagoofil.get_safe_file_name(
            "https://example.com/my%20report.pdf", self.save_directory
        )
        self.assertEqual(result, "my report.pdf")

    def test_trailing_slash_ignored(self) -> None:
        """A trailing slash is stripped before extracting the name.

        Args:
            None

        Returns:
            None
        """
        result = metagoofil.get_safe_file_name(
            "https://example.com/files/", self.save_directory
        )
        self.assertEqual(result, "files")

    def test_empty_names_rejected(self) -> None:
        """URLs with no usable file name return None.

        Args:
            None

        Returns:
            None
        """
        urls = [
            "https://example.com",
            "https://example.com/",
            "https://example.com/?a=b",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertIsNone(
                    metagoofil.get_safe_file_name(url, self.save_directory)
                )

    def test_traversal_components_rejected(self) -> None:
        """Dot and dot-dot names, plain or encoded, return None.

        Args:
            None

        Returns:
            None
        """
        urls = [
            "https://example.com/..",
            "https://example.com/.",
            "https://example.com/%2e%2e",
            "https://example.com/a/%2e%2e/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertIsNone(
                    metagoofil.get_safe_file_name(url, self.save_directory)
                )

    def test_encoded_separators_reduced_to_basename(self) -> None:
        """Encoded slashes and backslashes cannot escape the save directory.

        Args:
            None

        Returns:
            None
        """
        urls = [
            "https://example.com/..%2f..%2fetc%2fpasswd",
            "https://example.com/..%5c..%5cetc%5cpasswd",
            "https://example.com/%2fetc%2fpasswd",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    metagoofil.get_safe_file_name(url, self.save_directory),
                    "passwd",
                )

    def test_encoded_trailing_traversal_rejected(self) -> None:
        """A name that decodes to a path ending in .. returns None.

        Args:
            None

        Returns:
            None
        """
        urls = [
            "https://example.com/a%2f..",
            "https://example.com/a%5c..",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertIsNone(
                    metagoofil.get_safe_file_name(url, self.save_directory)
                )

    def test_nul_byte_rejected(self) -> None:
        """An encoded NUL byte returns None.

        Args:
            None

        Returns:
            None
        """
        result = metagoofil.get_safe_file_name(
            "https://example.com/report.pdf%00.txt", self.save_directory
        )
        self.assertIsNone(result)

    def test_symlink_escape_rejected(self) -> None:
        """A name that is a symlink pointing outside the save directory returns None.

        Args:
            None

        Returns:
            None
        """
        with tempfile.TemporaryDirectory() as outside_dir:
            link_path = os.path.join(self.save_directory, "evil.pdf")
            os.symlink(os.path.join(outside_dir, "target.pdf"), link_path)

            result = metagoofil.get_safe_file_name(
                "https://example.com/evil.pdf", self.save_directory
            )
            self.assertIsNone(result)

    def test_symlink_within_directory_allowed(self) -> None:
        """A symlink that stays inside the save directory is accepted.

        Args:
            None

        Returns:
            None
        """
        real_path = os.path.join(self.save_directory, "real.pdf")
        link_path = os.path.join(self.save_directory, "link.pdf")
        with open(real_path, "wb") as fh:
            fh.write(b"")
        os.symlink(real_path, link_path)

        # The link resolves to real.pdf in the same directory, so it is still contained.
        result = metagoofil.get_safe_file_name(
            "https://example.com/link.pdf", self.save_directory
        )
        self.assertEqual(result, "link.pdf")


if __name__ == "__main__":
    unittest.main()
