from __future__ import annotations

import asyncio
import copy
import html
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from api.index import (
    generate_gene_structure_svg,
    generate_multi_gene_structure_svg,
    generate_region_gene_structure_svg,
)
from api.models import (
    GeneStructureRequest,
    MultiGeneStructureRequest,
    RegionGeneStructureRequest,
)


OUTPUT_DIR = ROOT_DIR / "test_output_dir/svg-visual-review"
OUTPUT_HTML = OUTPUT_DIR / "index.html"


DRAW_SETTINGS = {
    "mode": "gene",
    "utr_color": "#f6b04f",
    "exon_color": "#7db7e8",
    "line_color": "#222222",
    "intron_shape": "straight",
}


def gene(
    transcript_id: str,
    *,
    strand: str = "+",
    start: int = 100,
    end: int = 900,
    exons: list[dict[str, int]] | None = None,
    cds: list[dict[str, int]] | None = None,
    five_prime_utrs: list[dict[str, int]] | None = None,
    three_prime_utrs: list[dict[str, int]] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    return {
        "transcript_id": transcript_id,
        "seq_id": "chr1",
        "source": "visual-review",
        "type": "mRNA",
        "start": start,
        "end": end,
        "score": None,
        "strand": strand,
        "phase": None,
        "attributes": {"ID": transcript_id},
        "total_length": end - start + 1,
        "exons": exons if exons is not None else [{"start": start, "end": end}],
        "cds": cds if cds is not None else [],
        "five_prime_utrs": five_prime_utrs if five_prime_utrs is not None else [],
        "three_prime_utrs": three_prime_utrs if three_prime_utrs is not None else [],
        "snps": [],
        "insertions": [],
        "deletion_regions": [],
        "domains": [],
        "protein_domains": [],
        **overrides,
    }


def single_payload(gene_structure: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    return {
        "draw_settings": copy.deepcopy(DRAW_SETTINGS),
        "gene_structure": gene_structure,
        "deletion_regions": [],
        "domains": [],
        "protein_domains": [],
        "snps": [],
        "insertions": [],
        "coordinate_mode": "relative",
        **overrides,
    }


SIMPLE_EXON_GENE = gene(
    "single-exon-only",
    start=100,
    end=600,
    exons=[{"start": 100, "end": 600}],
)

CDS_WITH_COMPUTED_UTR_GENE = gene(
    "computed-utr-from-exon-cds",
    start=100,
    end=900,
    exons=[{"start": 100, "end": 900}],
    cds=[{"start": 250, "end": 700}],
)

EXPLICIT_UTR_GENE = gene(
    "explicit-utr-cds",
    start=100,
    end=1000,
    exons=[
        {"start": 100, "end": 350},
        {"start": 500, "end": 1000},
    ],
    cds=[
        {"start": 200, "end": 350},
        {"start": 500, "end": 850},
    ],
    five_prime_utrs=[{"start": 100, "end": 199}],
    three_prime_utrs=[{"start": 851, "end": 1000}],
)

MINUS_STRAND_GENE = gene(
    "minus-strand",
    strand="-",
    start=1000,
    end=1900,
    exons=[
        {"start": 1000, "end": 1250},
        {"start": 1500, "end": 1900},
    ],
    cds=[
        {"start": 1100, "end": 1250},
        {"start": 1500, "end": 1750},
    ],
)

MULTI_EXON_GENE = gene(
    "multi-exon-intron",
    start=100,
    end=1400,
    exons=[
        {"start": 100, "end": 250},
        {"start": 500, "end": 700},
        {"start": 1050, "end": 1400},
    ],
    cds=[
        {"start": 150, "end": 250},
        {"start": 500, "end": 700},
        {"start": 1050, "end": 1250},
    ],
)

REGION_LEFT_GENE = gene(
    "region-left",
    start=1000,
    end=1900,
    exons=[
        {"start": 1000, "end": 1150},
        {"start": 1500, "end": 1900},
    ],
    cds=[
        {"start": 1080, "end": 1150},
        {"start": 1500, "end": 1750},
    ],
    five_prime_utrs=[{"start": 1000, "end": 1079}],
    three_prime_utrs=[{"start": 1751, "end": 1900}],
)

REGION_RIGHT_GENE = gene(
    "region-right",
    strand="-",
    start=2300,
    end=3200,
    exons=[
        {"start": 2300, "end": 2600},
        {"start": 2900, "end": 3200},
    ],
    cds=[
        {"start": 2450, "end": 2600},
        {"start": 2900, "end": 3080},
    ],
)


@dataclass(frozen=True)
class ReviewCase:
    title: str
    endpoint: str
    payload: dict[str, Any]
    notes: str


CASES: list[ReviewCase] = [
    ReviewCase(
        "Single gene: exon only",
        "single",
        single_payload(SIMPLE_EXON_GENE),
        "CDS/UTR を持たない exon だけの基本形。",
    ),
    ReviewCase(
        "Single gene: computed UTR from exon + CDS",
        "single",
        single_payload(CDS_WITH_COMPUTED_UTR_GENE),
        "exon と CDS だけを渡し、UTR が描画前に計算されるケース。",
    ),
    ReviewCase(
        "Single gene: explicit UTR/CDS",
        "single",
        single_payload(EXPLICIT_UTR_GENE),
        "明示的な 5'UTR、CDS、3'UTR、intron の表示確認。",
    ),
    ReviewCase(
        "Single gene: minus strand",
        "single",
        single_payload(MINUS_STRAND_GENE),
        "マイナス鎖での相対座標変換と方向の確認。",
    ),
    ReviewCase(
        "Single gene: multi exon / intron",
        "single",
        single_payload(MULTI_EXON_GENE),
        "複数 exon と長い intron の間隔確認。",
    ),
    ReviewCase(
        "Single gene: domain on relative coordinates",
        "single",
        single_payload(
            EXPLICIT_UTR_GENE,
            domains=[
                {"start": 180, "end": 420, "name": "Kinase", "color": "#6f42c1"},
                {"start": 620, "end": 760, "name": "ATPase", "color": "#198754"},
            ],
        ),
        "相対座標指定 domain の色、ラベル、重なり確認。",
    ),
    ReviewCase(
        "Single gene: protein domain coordinates",
        "single",
        single_payload(
            MULTI_EXON_GENE,
            protein_domains=[
                {"start": 5, "end": 45, "name": "PF00001"},
                {"start": 85, "end": 120, "name": "PF00002"},
            ],
        ),
        "アミノ酸座標から CDS 上へ変換される domain の確認。",
    ),
    ReviewCase(
        "Single gene: deletion with variants",
        "single",
        single_payload(
            EXPLICIT_UTR_GENE,
            deletion_regions=[{"start": 260, "end": 620, "color": "#d63384"}],
            domains=[{"start": 230, "end": 620, "name": "DeletedDomain", "color": "#fd7e14"}],
            snps=[{"position": 280, "color": "#111111"}, {"position": 760, "color": "#111111"}],
            insertions=[{"position": 300, "length": 12, "color": "#111111"}, {"position": 880, "length": 20, "color": "#111111"}],
        ),
        "deletion と重なる feature/SNP/insertion がどう残るかを確認。",
    ),
    ReviewCase(
        "Single gene: absolute coordinate mode",
        "single",
        single_payload(
            gene(
                "absolute-coordinate",
                start=10000,
                end=11200,
                exons=[
                    {"start": 10000, "end": 10200},
                    {"start": 10800, "end": 11200},
                ],
                cds=[
                    {"start": 10080, "end": 10200},
                    {"start": 10800, "end": 11050},
                ],
            ),
            coordinate_mode="absolute",
            snps=[{"position": 10900, "color": "#111111"}],
            deletion_regions=[{"start": 10100, "end": 10150, "color": "#dc3545"}],
        ),
        "絶対座標指定の SNP/deletion と軸ラベルの確認。",
    ),
    ReviewCase(
        "Multi gene: stacked comparison",
        "multi",
        {
            "draw_settings": copy.deepcopy(DRAW_SETTINGS),
            "items": [
                {"gene_structure": EXPLICIT_UTR_GENE, "domains": [{"start": 220, "end": 360, "name": "A", "color": "#6f42c1"}]},
                {"gene_structure": MULTI_EXON_GENE, "snps": [{"position": 540, "color": "#111111"}]},
                {"gene_structure": MINUS_STRAND_GENE, "insertions": [{"position": 1200, "length": 18, "color": "#111111"}]},
            ],
            "show_labels": True,
            "show_scale": True,
            "gene_spacing": 45,
            "label_spacing": 12,
            "coordinate_mode": "relative",
        },
        "複数 transcript を縦に並べた比較表示。",
    ),
    ReviewCase(
        "Region gene: shared genomic axis",
        "region",
        {
            "draw_settings": copy.deepcopy(DRAW_SETTINGS),
            "gene_structures": [
                REGION_LEFT_GENE,
                REGION_RIGHT_GENE,
            ],
            "region_start": 900,
            "region_end": 3300,
            "show_labels": True,
            "gene_spacing": 45,
            "label_spacing": 12,
        },
        "共通のゲノム領域上に複数 gene を配置する表示。",
    ),
]


ENDPOINTS: dict[str, tuple[type[BaseModel], Callable[[Any], Awaitable[Response]]]] = {
    "single": (GeneStructureRequest, generate_gene_structure_svg),
    "multi": (MultiGeneStructureRequest, generate_multi_gene_structure_svg),
    "region": (RegionGeneStructureRequest, generate_region_gene_structure_svg),
}


def json_pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


async def render_case(case: ReviewCase) -> dict[str, Any]:
    model_cls, endpoint = ENDPOINTS[case.endpoint]
    try:
        request = model_cls.model_validate(case.payload)
        response = await endpoint(request)
        svg = response.body.decode("utf-8")
        return {"ok": True, "svg": svg}
    except (ValidationError, HTTPException, Exception) as exc:
        return {"ok": False, "error": repr(exc)}


def case_card(case: ReviewCase, result: dict[str, Any], index: int) -> str:
    payload = html.escape(json_pretty(case.payload))
    notes = html.escape(case.notes)
    status = "ok" if result["ok"] else "error"
    body = result["svg"] if result["ok"] else f"<pre>{html.escape(result['error'])}</pre>"

    return f"""
    <section class="case {status}">
      <header>
        <div>
          <p class="case-index">Case {index:02d}</p>
          <h2>{html.escape(case.title)}</h2>
        </div>
        <span class="badge">{html.escape(case.endpoint)}</span>
      </header>
      <p class="notes">{notes}</p>
      <div class="svg-frame">{body}</div>
      <details>
        <summary>Input JSON</summary>
        <pre>{payload}</pre>
      </details>
    </section>
    """


def build_html(cards: list[str], failed_count: int) -> str:
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SVG Visual Review</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --ink: #1f2328;
      --muted: #667085;
      --line: #d0d7de;
      --panel: #ffffff;
      --accent: #0f766e;
      --danger: #b42318;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 22px 18px 40px;
    }}
    .topline {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 24px;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 14px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.2;
    }}
    .summary {{
      margin: 0;
      color: var(--muted);
    }}
    .result {{
      font-weight: 700;
      color: {html.escape("var(--danger)" if failed_count else "var(--accent)")};
      white-space: nowrap;
    }}
    .case {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 12px 0;
      padding: 14px;
    }}
    .case.error {{
      border-color: #f2a19b;
    }}
    .case header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }}
    .case-index {{
      margin: 0 0 4px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    h2 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.3;
    }}
    .badge {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 10px;
      color: var(--muted);
      font-size: 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .notes {{
      margin: 8px 0 10px;
      color: var(--muted);
    }}
    .svg-frame {{
      overflow: auto;
      border: 1px solid var(--line);
      background: #fff;
      min-height: 150px;
      padding: 8px;
    }}
    .svg-frame svg {{
      max-width: none;
      height: auto;
    }}
    details {{
      margin-top: 8px;
    }}
    summary {{
      cursor: pointer;
      color: var(--accent);
      font-weight: 600;
    }}
    pre {{
      overflow: auto;
      background: #f6f8fa;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      font-size: 12px;
      line-height: 1.45;
    }}
  </style>
</head>
<body>
  <main>
    <div class="topline">
      <div>
        <h1>SVG Visual Review</h1>
        <p class="summary">Input JSON と生成 SVG を並べた、手元確認用の一時レポートです。</p>
      </div>
      <div class="result">{len(cards)} cases / {failed_count} failed</div>
    </div>
    {"".join(cards)}
  </main>
</body>
</html>
"""


async def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = await asyncio.gather(*(render_case(case) for case in CASES))
    failed_count = sum(1 for result in results if not result["ok"])
    cards = [
        case_card(case, result, index)
        for index, (case, result) in enumerate(zip(CASES, results), start=1)
    ]

    OUTPUT_HTML.write_text(build_html(cards, failed_count), encoding="utf-8")
    print(f"Wrote {OUTPUT_HTML}")
    print(f"{len(CASES)} cases / {failed_count} failed")
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
