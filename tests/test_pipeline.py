from __future__ import annotations

from src.pipeline import run_pipeline


def test_pipeline_generates_data_reports_and_figures(sample_data, tmp_path):
    raw_path = tmp_path / "European_Bank.csv"
    sample_data.to_csv(raw_path, index=False)
    processed_path = tmp_path / "processed" / "cleaned_dataset.csv"
    output_dir = tmp_path / "outputs"
    figure_dir = tmp_path / "reports" / "figures"
    report_dir = tmp_path / "reports"

    result = run_pipeline(
        raw_data_path=raw_path,
        processed_data_path=processed_path,
        output_dir=output_dir,
        figure_dir=figure_dir,
        report_dir=report_dir,
    )

    assert processed_path.exists()
    assert (output_dir / "overall_kpis.csv").exists()
    assert (output_dir / "segment_summary.csv").exists()
    assert (report_dir / "research_paper.md").exists()
    assert (report_dir / "executive_summary.md").exists()
    assert (report_dir / "data_quality_report.md").exists()
    assert len(list(figure_dir.glob("*.png"))) >= 6
    figure_names = {path.name for path in result["figure_paths"]}
    assert "product_activity_interaction.png" in figure_names
    assert "segment_risk_matrix.png" in figure_names
    assert result["kpis"]["total_customers"] == len(sample_data)
