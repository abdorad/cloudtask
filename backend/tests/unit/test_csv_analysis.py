import pytest

from app.core.errors import CsvAnalysisError
from app.worker.csv_analysis import analyze_csv


def test_analyze_csv_returns_profile_and_numeric_statistics():
    report = analyze_csv(
        b"name,age,score\nAda,31,9.5\nGrace,,10.5\n",
        "c508c8af-2aec-4358-8cd5-2bf81c9c0cf1",
    )

    assert report["rowCount"] == 2
    assert report["columns"] == ["name", "age", "score"]
    assert report["estimatedTypes"] == {"name": "string", "age": "integer", "score": "number"}
    assert report["missingValues"]["age"] == 1
    assert report["numericStatistics"]["score"]["mean"] == 10.0


def test_analyze_csv_rejects_inconsistent_rows():
    with pytest.raises(CsvAnalysisError, match="different number of fields"):
        analyze_csv(b"name,age\nAda,31,extra\n", "c508c8af-2aec-4358-8cd5-2bf81c9c0cf1")
