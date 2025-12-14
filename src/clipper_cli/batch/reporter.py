"""Batch processing report generator."""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

from clipper_cli.models import BatchResult, VideoResult
from clipper_cli.utils.console import (
    console,
    format_time,
    format_duration,
    create_batch_summary_panel,
)


class BatchReporter:
    """Generate reports for batch processing results."""
    
    def __init__(self, output_dir: str = "./output"):
        """Initialize reporter.
        
        Args:
            output_dir: Directory to save reports.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        result: BatchResult,
        format: str = "json",
    ) -> str:
        """Generate a report for batch processing results.
        
        Args:
            result: Batch processing result.
            format: Report format (json, csv, html).
        
        Returns:
            Path to generated report file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            return self._generate_json_report(result, timestamp)
        elif format == "csv":
            return self._generate_csv_report(result, timestamp)
        elif format == "html":
            return self._generate_html_report(result, timestamp)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _generate_json_report(
        self,
        result: BatchResult,
        timestamp: str,
    ) -> str:
        """Generate JSON report."""
        report_path = self.output_dir / f"batch_report_{timestamp}.json"
        
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_videos": result.total_videos,
                "successful": result.successful,
                "failed": result.failed,
                "total_clips": result.total_clips,
                "processing_time_seconds": result.processing_time,
                "processing_time_formatted": format_duration(result.processing_time),
            },
            "videos": [],
            "errors": result.errors,
            "top_clips": [],
        }
        
        # Add video details
        for video_result in result.results:
            video_data = {
                "source_file": video_result.source_file,
                "success": video_result.success,
                "processing_time": video_result.processing_time,
                "transcriber": video_result.transcriber_used.value,
                "llm_provider": video_result.llm_provider_used.value,
                "llm_model": video_result.llm_model_used,
                "clips": [],
            }
            
            if video_result.transcript:
                video_data["language"] = video_result.transcript.language
                video_data["duration"] = video_result.transcript.duration
            
            for clip_result in video_result.clips:
                if clip_result.success:
                    video_data["clips"].append({
                        "output_file": clip_result.output_file,
                        "start": clip_result.clip.start,
                        "end": clip_result.clip.end,
                        "duration": clip_result.clip.duration,
                        "score": clip_result.clip.score.total_score,
                        "viral_factor": clip_result.clip.viral_factor,
                        "reason": clip_result.clip.reason,
                        "caption": clip_result.clip.suggested_caption,
                    })
            
            if video_result.error:
                video_data["error"] = video_result.error
            
            report_data["videos"].append(video_data)
        
        # Find top clips across all videos
        all_clips = []
        for video_result in result.results:
            for clip_result in video_result.clips:
                if clip_result.success:
                    all_clips.append({
                        "file": clip_result.output_file,
                        "source": video_result.source_file,
                        "score": clip_result.clip.score.total_score,
                        "viral_factor": clip_result.clip.viral_factor,
                    })
        
        all_clips.sort(key=lambda x: x["score"], reverse=True)
        report_data["top_clips"] = all_clips[:10]
        
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        return str(report_path)
    
    def _generate_csv_report(
        self,
        result: BatchResult,
        timestamp: str,
    ) -> str:
        """Generate CSV report."""
        report_path = self.output_dir / f"batch_report_{timestamp}.csv"
        
        with open(report_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Source Video",
                "Clip File",
                "Start Time",
                "End Time",
                "Duration",
                "Score",
                "Viral Factor",
                "Caption",
            ])
            
            # Data rows
            for video_result in result.results:
                for clip_result in video_result.clips:
                    if clip_result.success:
                        writer.writerow([
                            video_result.source_file,
                            clip_result.output_file,
                            format_time(clip_result.clip.start),
                            format_time(clip_result.clip.end),
                            f"{clip_result.clip.duration:.1f}s",
                            f"{clip_result.clip.score.total_score:.1f}",
                            clip_result.clip.viral_factor,
                            clip_result.clip.suggested_caption or "",
                        ])
        
        return str(report_path)
    
    def _generate_html_report(
        self,
        result: BatchResult,
        timestamp: str,
    ) -> str:
        """Generate HTML report."""
        report_path = self.output_dir / f"batch_report_{timestamp}.html"
        
        # Find top clips
        all_clips = []
        for video_result in result.results:
            for clip_result in video_result.clips:
                if clip_result.success:
                    all_clips.append((video_result, clip_result))
        
        all_clips.sort(key=lambda x: x[1].clip.score.total_score, reverse=True)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clipper CLI - Batch Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat {{
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #00d9ff;
        }}
        .stat-label {{ color: #888; margin-top: 0.5rem; }}
        .section {{ margin-bottom: 2rem; }}
        .section-title {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #00ff88;
        }}
        .clips-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1rem;
        }}
        .clip-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .clip-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        .clip-score {{
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: bold;
            color: #000;
        }}
        .clip-file {{ font-weight: bold; color: #00d9ff; }}
        .clip-meta {{ color: #888; font-size: 0.9rem; margin: 0.5rem 0; }}
        .clip-factor {{
            display: inline-block;
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        .clip-caption {{
            margin-top: 0.5rem;
            font-style: italic;
            color: #aaa;
        }}
        .errors {{
            background: rgba(255, 100, 100, 0.1);
            border: 1px solid rgba(255, 100, 100, 0.3);
            border-radius: 12px;
            padding: 1rem;
        }}
        .error-item {{ margin: 0.5rem 0; color: #ff6b6b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📹 Clipper CLI - Batch Report</h1>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{result.total_videos}</div>
                <div class="stat-label">Total Videos</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.successful}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.total_clips}</div>
                <div class="stat-label">Total Clips</div>
            </div>
            <div class="stat">
                <div class="stat-value">{format_duration(result.processing_time)}</div>
                <div class="stat-label">Processing Time</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🏆 Top Clips</h2>
            <div class="clips-grid">
                {"".join(self._render_clip_card(vr, cr) for vr, cr in all_clips[:10])}
            </div>
        </div>
        
        {"" if not result.errors else f'''
        <div class="section">
            <h2 class="section-title">❌ Errors</h2>
            <div class="errors">
                {"".join(f'<div class="error-item"><strong>{k}:</strong> {v}</div>' for k, v in result.errors.items())}
            </div>
        </div>
        '''}
        
        <p style="text-align: center; color: #666; margin-top: 2rem;">
            Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>
    </div>
</body>
</html>"""
        
        with open(report_path, "w") as f:
            f.write(html)
        
        return str(report_path)
    
    def _render_clip_card(self, video_result: VideoResult, clip_result) -> str:
        """Render a single clip card for HTML report."""
        clip = clip_result.clip
        return f"""
        <div class="clip-card">
            <div class="clip-header">
                <span class="clip-file">{Path(clip_result.output_file).name}</span>
                <span class="clip-score">{clip.score.total_score:.1f}</span>
            </div>
            <div class="clip-meta">
                {format_time(clip.start)} - {format_time(clip.end)} ({clip.duration:.1f}s)
            </div>
            <div class="clip-meta">
                Source: {Path(video_result.source_file).name}
            </div>
            <span class="clip-factor">{clip.viral_factor}</span>
            {f'<div class="clip-caption">"{clip.suggested_caption}"</div>' if clip.suggested_caption else ''}
        </div>
        """
    
    def print_summary(self, result: BatchResult) -> None:
        """Print batch summary to console."""
        console.print()
        console.print(create_batch_summary_panel(result))
        
        # Show top clips
        if result.results:
            all_clips = []
            for video_result in result.results:
                for clip_result in video_result.clips:
                    if clip_result.success:
                        all_clips.append(clip_result)
            
            if all_clips:
                all_clips.sort(key=lambda c: c.clip.score.total_score, reverse=True)
                
                console.print("\n🏆 [bold]Top Clips Across All Videos:[/bold]")
                for i, clip in enumerate(all_clips[:5], 1):
                    console.print(
                        f"   {i}. [cyan]{Path(clip.output_file).name}[/cyan] "
                        f"(Score: [magenta]{clip.clip.score.total_score:.1f}[/magenta])"
                    )
