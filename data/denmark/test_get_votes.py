import csv
import json
import runpy
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODULE = runpy.run_path(str(HERE / "get-votes.py"))


class DanishDataTests(unittest.TestCase):
    def page(self, fixed_only=False):
        headings = (["Parti", "Antal", "Pct.", "Kreds-<br>man-<br>dater", ""]
                    if fixed_only else
                    ["Parti", "Antal", "Pct.", "Man-<br>dater",
                     "Kreds-<br>man-<br>dater", "Till\u00e6gs-<br>man-<br>dater"])
        numbers = ["1.234", "100%", "2", ""] if fixed_only else ["1.234", "100%", "3", "2", "1"]
        html = '<table><tr><td><table class="valgopg_tabel">'
        html += '<tr><td colspan="6">Stemmer</td></tr><tr>'
        html += "".join(f"<td>{h}</td>" for h in headings) + "</tr>"
        # The source omits some closing td tags in spacer rows.
        html += '<tr><td class="tablestartspacer"></tr>'
        html += '<tr><td class="vaelgeropg_parti">A. Party</td>'
        html += "".join(f"<td>{n}</td>" for n in numbers) + "</tr>"
        html += '<tr><td class="vaelgeropg_parti">I alt gyldige stemmer</td><td>1.234</td></tr>'
        html += '</table></td></tr></table>'
        return MODULE["ResultPage"](html)

    def test_full_and_fixed_only_result_tables(self):
        for fixed_only in (False, True):
            with self.subTest(fixed_only=fixed_only):
                result = MODULE["result"](self.page(fixed_only), "Test", "test.htm")
                self.assertEqual(result["valid_votes"], 1234)
                self.assertEqual(result["parties"]["A. Party"]["fixed_seats"], 2)
                self.assertEqual(result["parties"]["A. Party"]["adjustment_seats"],
                                 0 if fixed_only else 1)
                self.assertEqual(result["parties"][MODULE["INDEPENDENTS"]]["votes"], 0)

    def test_missing_votes_are_rejected(self):
        page = self.page()
        page.tables[0][-1][1]["text"] = "1.235"
        with self.assertRaisesRegex(ValueError, "Votes do not sum"):
            MODULE["result"](page, "Test", "test.htm")

    def test_malformed_counts_are_rejected(self):
        for value in ("", "1.23", "1,234", "-2", "n/a"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MODULE["integer"](value)

    def test_csv_preserves_official_votes_and_metadata(self):
        official = json.loads((HERE / "official-results_2026.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "votes.csv"
            MODULE["write_votes"](official, path)
            with path.open(encoding="utf-8", newline="") as file:
                rows = list(csv.reader(file))
        self.assertEqual(len(rows[0]), 23)
        self.assertEqual(rows[1][13], "Venstre, Danmarks Liberale Parti")
        self.assertEqual(rows[2][5:], ["0"] * 12 + ["1"] * 6)
        self.assertEqual(rows[3][3], "40")
        self.assertEqual(sum(sum(map(int, r[5:])) for r in rows[4:14]), 3567625)
        for row, district in zip(rows[4:14], official["constituencies"]):
            self.assertEqual(row[0], district["name"])
            self.assertEqual(row[2:5], ["0", "", district["region"]])
            self.assertEqual(sum(map(int, row[5:])), district["valid_votes"])
            self.assertEqual(sum(map(int, row[17:])),
                             district["parties"][MODULE["INDEPENDENTS"]]["votes"])
        self.assertEqual([r[:3] for r in rows[-3:]], [
            ["H", "Hovedstaden", "12"],
            ["SS", "Sj\u00e6lland-Syddanmark", "14"],
            ["MN", "Midtjylland-Nordjylland", "14"],
        ])


if __name__ == "__main__":
    unittest.main()
