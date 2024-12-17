import unittest
from unittest.mock import patch, MagicMock, call
from database.load_data import connect_to_db, get_or_insert_unknown_subject

class TestLoadData(unittest.TestCase):

    @patch('psycopg2.connect')
    def test_connect_to_db_success(self, mock_connect):
        """Test successful database connection."""
        mock_connect.return_value = MagicMock()
        connection = connect_to_db()
        self.assertIsNotNone(connection)
        mock_connect.assert_called_once()

    @patch('psycopg2.connect')
    def test_connect_to_db_failure(self, mock_connect):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        connection = connect_to_db()
        self.assertIsNone(connection)
        mock_connect.assert_called_once()

    @patch('psycopg2.connect')
    def test_get_or_insert_unknown_subject_existing(self, mock_connect):
        """Test when 'Unknown' subject already exists in the database."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)

        mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        connection = mock_connect()
        cursor = connection.cursor().__enter__()
        subject_id = get_or_insert_unknown_subject(cursor)
        self.assertEqual(subject_id, 1)

        mock_cursor.execute.assert_called_with(
            "SELECT subject_id FROM subjects WHERE name = %s;", ('Unknown',)
        )


if __name__ == '__main__':
    unittest.main()