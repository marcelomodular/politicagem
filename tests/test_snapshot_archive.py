import json
import shutil
import tempfile
import unittest
from pathlib import Path

from app import app
from snapshot_archive import (
    build_archive_payload,
    build_calendar_data,
    list_snapshots,
    resolve_snapshot_file,
    resolve_snapshot_path,
)


class SnapshotArchiveTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.app = app.test_client()
        self.app.testing = True

        # Criar dois snapshots de teste com datas distintas
        self.snap1 = self.temp_dir / "2026-10-28-100000"
        self.snap1.mkdir(parents=True)
        (self.snap1 / "index.html").write_text("<html>Edição 28</html>", encoding="utf-8")
        (self.snap1 / "snapshot_metadata.json").write_text(
            json.dumps({"news_count": 10, "articles_generated": 10, "correct_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"}),
            encoding="utf-8"
        )
        vis1 = self.snap1 / "visualizar"
        vis1.mkdir()
        (vis1 / "artigo-0.html").write_text("<html>Artigo 0</html>", encoding="utf-8")

        self.snap2 = self.temp_dir / "2026-10-29-153000"
        self.snap2.mkdir(parents=True)
        (self.snap2 / "index.html").write_text("<html>Edição 29</html>", encoding="utf-8")
        (self.snap2 / "snapshot_metadata.json").write_text(
            json.dumps({"news_count": 15, "articles_generated": 15}),
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_snapshots_extracts_metadata_and_dates(self):
        items = list_snapshots(base_dir=self.temp_dir)
        self.assertEqual(len(items), 2)
        # Mais recente primeiro
        self.assertEqual(items[0]["slug"], "2026-10-29-153000")
        self.assertEqual(items[0]["data_iso"], "2026-10-29")
        self.assertEqual(items[0]["ano"], 2026)
        self.assertEqual(items[0]["mes"], 10)
        self.assertEqual(items[0]["dia"], 29)
        self.assertEqual(items[0]["noticias"], 15)

        self.assertEqual(items[1]["slug"], "2026-10-28-100000")
        self.assertEqual(items[1]["cid"], "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG")

    def test_build_calendar_data_groups_by_day(self):
        items = list_snapshots(base_dir=self.temp_dir)
        cal = build_calendar_data(items)

        self.assertIn("2026-10-29", cal["days_map"])
        self.assertIn("2026-10-28", cal["days_map"])
        self.assertEqual(len(cal["days_map"]["2026-10-29"]), 1)
        self.assertEqual(cal["years"], [2026])
        self.assertEqual(cal["latest_date"], "2026-10-29")

    def test_build_archive_payload_serializable(self):
        payload = build_archive_payload(base_dir=self.temp_dir)
        self.assertEqual(payload["total"], 2)
        self.assertIn("calendar", payload)
        self.assertIn("days_map", payload["calendar"])
        # Garante que JSON dumps não quebra
        serialized = json.dumps(payload)
        self.assertIn("2026-10-29", serialized)

    def test_resolve_snapshot_file_safety(self):
        # Arquivo raiz
        dir_path, rel = resolve_snapshot_file("2026-10-28-100000", "index.html", base_dir=self.temp_dir)
        self.assertEqual(rel, "index.html")

        # Subarquivo
        dir_path, rel = resolve_snapshot_file("2026-10-28-100000", "visualizar/artigo-0.html", base_dir=self.temp_dir)
        self.assertEqual(rel, "visualizar/artigo-0.html")

        # Tentativa de Path Traversal
        with self.assertRaises(ValueError):
            resolve_snapshot_file("2026-10-28-100000", "../../etc/passwd", base_dir=self.temp_dir)

    def test_api_arquivo_endpoint(self):
        res = self.app.get('/api/arquivo')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total", data)
        self.assertIn("calendar", data)
        self.assertIn("days_map", data["calendar"])

    def test_arquivo_html_view(self):
        res = self.app.get('/arquivo')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Calendário Histórico das Edições", html)
        self.assertIn("cal-grid", html)
        self.assertIn("view-calendar", html)


if __name__ == '__main__':
    unittest.main()
