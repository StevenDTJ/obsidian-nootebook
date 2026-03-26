#!/usr/bin/env python3
"""Convert local documents to MinerU outputs (markdown/html/docx/json/latex)."""

from __future__ import annotations

import argparse
import glob
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

FORMAT_ALIASES = {
    "md": "markdown",
    "markdown": "markdown",
    "json": "json",
    "html": "html",
    "docx": "docx",
    "latex": "latex",
    "tex": "latex",
}

EXTRA_FORMATS = {"html", "docx", "latex"}
TERMINAL_STATES = {"done", "failed"}
EXTENSIONS = {
    "markdown": {".md"},
    "json": {".json"},
    "html": {".html", ".htm"},
    "docx": {".docx"},
    "latex": {".tex"},
}

MD_IMAGE_LINK_PATTERN = re.compile(r"!\[([^\]]*)\]\((<[^>]+>|[^)\s]+)(\s+\"[^\"]*\")?\)")
HTML_IMG_SRC_PATTERN = re.compile(r"(<img\\b[^>]*?\\bsrc\\s*=\\s*)([\"\'])([^\"\']+)(\\2)", re.IGNORECASE)
WINDOWS_ABS_PATH_PATTERN = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")
URL_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class MineruError(RuntimeError):
    """MinerU API or workflow error."""


def _http_json(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json_payload: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    body = None
    req_headers = dict(headers or {})
    if json_payload is not None:
        body = json.dumps(json_payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    req = Request(url=url, data=body, method=method, headers=req_headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise MineruError(f"HTTP {exc.code} for {url}: {detail}") from exc
    except URLError as exc:
        raise MineruError(f"Network error for {url}: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MineruError(f"Invalid JSON response from {url}: {raw[:500]}") from exc


def _http_put_binary(url: str, file_path: Path, *, timeout: int = 120) -> None:
    data = file_path.read_bytes()
    req = Request(
        url=url,
        data=data,
        method="PUT",
        headers={"Content-Type": ""},
    )
    try:
        with urlopen(req, timeout=timeout):
            return
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise MineruError(f"Upload failed for {file_path.name}: HTTP {exc.code}, {detail}") from exc
    except URLError as exc:
        raise MineruError(f"Upload network error for {file_path.name}: {exc}") from exc


def _download_file(url: str, dest: Path, *, timeout: int = 120) -> None:
    req = Request(url=url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as fp:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    fp.write(chunk)
            return
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise MineruError(f"Download failed ({url}): HTTP {exc.code}, {detail}") from exc
    except URLError:
        # Fallback for environments where urlopen has TLS/proxy issues for CDN links.
        curl_path = shutil.which("curl") or shutil.which("curl.exe")
        if not curl_path:
            raise MineruError(f"Download network error ({url}). urlopen failed and curl is unavailable.")

        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = [curl_path, "-fL", "--max-time", str(timeout), "--output", str(dest), url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return

        stderr = (result.stderr or "").strip()
        raise MineruError(f"Download failed via curl ({url}): {stderr}")


def _load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise MineruError(
            f"Config file not found: {config_path}. "
            "Copy mineru_config.example.json to mineru_config.json and fill api_key first."
        )

    try:
        raw = config_path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except UnicodeDecodeError as exc:
        raise MineruError(f"Config must be UTF-8 text: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise MineruError(f"Invalid JSON in config file: {config_path}") from exc

    if not isinstance(data, dict):
        raise MineruError(f"Config must be a JSON object: {config_path}")
    return data


def _parse_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _normalize_formats(raw: str) -> Set[str]:
    if not raw.strip():
        raise MineruError("At least one format is required.")

    normalized: Set[str] = set()
    for part in raw.split(","):
        token = part.strip().lower()
        if not token:
            continue
        canonical = FORMAT_ALIASES.get(token)
        if canonical is None:
            allowed = ", ".join(sorted(set(FORMAT_ALIASES.keys())))
            raise MineruError(f"Unsupported format '{token}'. Allowed: {allowed}")
        normalized.add(canonical)

    if not normalized:
        raise MineruError("No valid formats found.")
    return normalized


def _collect_input_files(items: Sequence[str]) -> List[Path]:
    seen = set()
    files: List[Path] = []

    for item in items:
        path = Path(item)
        candidates: List[Path]
        if path.exists() and path.is_file():
            candidates = [path.resolve()]
        else:
            candidates = [Path(m).resolve() for m in glob.glob(item, recursive=True) if Path(m).is_file()]

        for candidate in candidates:
            key = str(candidate).lower()
            if key in seen:
                continue
            seen.add(key)
            files.append(candidate)

    if not files:
        raise MineruError("No input files found. Check file paths or glob patterns.")
    return files


def _api_root(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.netloc:
        cleaned = f"{parsed.scheme}://{parsed.netloc}"
    return f"{cleaned}/api/v4"


def _create_batch(
    *,
    base_url: str,
    api_key: str,
    files: Sequence[Path],
    formats: Set[str],
    is_ocr: bool,
    language: str,
    enable_formula: bool,
    timeout: int,
) -> Dict[str, Any]:
    request_files = []
    for path in files:
        request_files.append(
            {
                "name": path.name,
                "is_ocr": is_ocr,
                "data_id": uuid.uuid4().hex,
            }
        )

    extra_formats = sorted(fmt for fmt in formats if fmt in EXTRA_FORMATS)
    payload: Dict[str, Any] = {
        "enable_formula": enable_formula,
        "language": language,
        "files": request_files,
    }
    if extra_formats:
        payload["extra_formats"] = extra_formats

    headers = {"Authorization": f"Bearer {api_key}"}
    resp = _http_json(
        "POST",
        f"{_api_root(base_url)}/file-urls/batch",
        headers=headers,
        json_payload=payload,
        timeout=timeout,
    )

    data = resp.get("data") or {}
    batch_id = data.get("batch_id")
    file_urls = data.get("file_urls") or []
    if not batch_id or not file_urls:
        raise MineruError(f"Unexpected create-batch response: {resp}")

    url_map = {}
    if isinstance(file_urls, list):
        for idx, item in enumerate(file_urls):
            if isinstance(item, dict):
                data_id = item.get("data_id")
                url = item.get("url")
            elif isinstance(item, str):
                data_id = request_files[idx]["data_id"] if idx < len(request_files) else None
                url = item
            else:
                data_id = None
                url = None

            if data_id and url:
                url_map[data_id] = url
    elif isinstance(file_urls, dict):
        for data_id, url in file_urls.items():
            if data_id and isinstance(url, str):
                url_map[str(data_id)] = url

    if len(url_map) != len(request_files):
        raise MineruError(
            f"Mismatch between requested files ({len(request_files)}) and upload urls ({len(url_map)})."
        )

    return {
        "batch_id": batch_id,
        "request_files": request_files,
        "url_map": url_map,
    }


def _upload_files(
    *,
    files: Sequence[Path],
    request_files: Sequence[Dict[str, Any]],
    url_map: Dict[str, str],
    timeout: int,
) -> None:
    for file_path, info in zip(files, request_files):
        data_id = info["data_id"]
        upload_url = url_map.get(data_id)
        if not upload_url:
            raise MineruError(f"Missing upload url for {file_path.name}.")
        _http_put_binary(upload_url, file_path, timeout=timeout)
        print(f"Uploaded: {file_path}")


def _fetch_batch_results(
    *,
    base_url: str,
    api_key: str,
    batch_id: str,
    timeout: int,
) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}"}
    start = 0
    all_results: List[Dict[str, Any]] = []
    batch_zip_url = None

    while True:
        query = urlencode({"start": start, "limit": 100})
        resp = _http_json(
            "GET",
            f"{_api_root(base_url)}/extract-results/batch/{batch_id}?{query}",
            headers=headers,
            timeout=timeout,
        )

        data = resp.get("data") or {}
        extract_result = data.get("extract_result") or []
        all_results.extend(extract_result)
        if not batch_zip_url:
            batch_zip_url = data.get("full_zip_url")

        next_start = data.get("next_start")
        if next_start in (None, "", -1):
            break

        try:
            next_start_int = int(next_start)
        except (TypeError, ValueError):
            break

        if next_start_int <= start:
            break
        start = next_start_int

    return {"extract_result": all_results, "full_zip_url": batch_zip_url}


def _is_all_terminal(results: Sequence[Dict[str, Any]], expected_count: int) -> bool:
    if len(results) < expected_count:
        return False
    states = [str(item.get("state", "")).strip().lower() for item in results[:expected_count]]
    return all(state in TERMINAL_STATES for state in states)


def _collect_files_by_format(root: Path, formats: Set[str]) -> List[Path]:
    allowed_exts = set()
    for fmt in formats:
        allowed_exts.update(EXTENSIONS.get(fmt, set()))

    selected: List[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in allowed_exts:
            selected.append(path)

    return sorted(selected)


def _to_absolute_asset_target(target: str, markdown_dir: Path) -> Optional[str]:
    cleaned = target.strip()
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1].strip()

    if not cleaned:
        return None
    if cleaned.startswith(("#", "data:", "mailto:", "tel:", "file://", "http://", "https://", "//")):
        return None
    if WINDOWS_ABS_PATH_PATTERN.match(cleaned):
        return None
    if URL_SCHEME_PATTERN.match(cleaned):
        return None

    m = re.match(r"^([^?#]+)([?#].*)?$", cleaned)
    if m:
        path_part = m.group(1)
        suffix_part = m.group(2) or ""
    else:
        path_part = cleaned
        suffix_part = ""

    absolute = (markdown_dir / Path(path_part)).resolve().as_posix()
    return f"{absolute}{suffix_part}"


def _rewrite_markdown_images_to_absolute(markdown_file: Path) -> int:
    try:
        original = markdown_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        original = markdown_file.read_text(encoding="utf-8-sig")

    changes = 0

    def repl_md(match: re.Match[str]) -> str:
        nonlocal changes
        alt_text = match.group(1)
        target = match.group(2)
        title = match.group(3) or ""
        absolute = _to_absolute_asset_target(target, markdown_file.parent)
        if not absolute:
            return match.group(0)
        changes += 1
        return f"![{alt_text}](<{absolute}>{title})"

    rewritten = MD_IMAGE_LINK_PATTERN.sub(repl_md, original)

    def repl_html(match: re.Match[str]) -> str:
        nonlocal changes
        prefix = match.group(1)
        quote = match.group(2)
        src = match.group(3)
        absolute = _to_absolute_asset_target(src, markdown_file.parent)
        if not absolute:
            return match.group(0)
        changes += 1
        return f"{prefix}{quote}{absolute}{quote}"

    rewritten = HTML_IMG_SRC_PATTERN.sub(repl_html, rewritten)

    if rewritten != original:
        markdown_file.write_text(rewritten, encoding="utf-8")

    return changes


def _download_and_extract(
    *,
    results: Sequence[Dict[str, Any]],
    output_dir: Path,
    formats: Set[str],
    timeout: int,
    keep_zip: bool,
) -> List[Path]:
    generated: List[Path] = []

    for idx, item in enumerate(results, start=1):
        state = str(item.get("state", "")).strip().lower()
        if state != "done":
            continue

        zip_url = item.get("full_zip_url")
        if not zip_url:
            continue

        file_name = str(item.get("file_name") or f"file-{idx}")
        stem = Path(file_name).stem or f"file-{idx}"

        zip_path = output_dir / f"{stem}.zip"
        extract_dir = output_dir / stem

        _download_file(zip_url, zip_path, timeout=timeout)
        print(f"Downloaded: {zip_path}")

        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        if "markdown" in formats:
            markdown_files = _collect_files_by_format(extract_dir, {"markdown"})
            rewritten_count = 0
            for markdown_file in markdown_files:
                rewritten_count += _rewrite_markdown_images_to_absolute(markdown_file)
            if rewritten_count:
                print(f"Rewrote {rewritten_count} markdown image reference(s) to absolute paths.")

        generated.extend(_collect_files_by_format(extract_dir, formats))

        if not keep_zip:
            zip_path.unlink(missing_ok=True)

    return sorted(set(generated))


def _default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "mineru_config.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert documents with MinerU API and download markdown/html/docx/json outputs."
    )
    parser.add_argument("inputs", nargs="+", help="Input files or glob patterns.")
    parser.add_argument("--config", default=str(_default_config_path()), help="Path to mineru config JSON.")
    parser.add_argument("--api-key", default="", help="Override API key from config.")
    parser.add_argument("--formats", default="", help="Comma-separated formats, e.g. markdown,html,docx,json")
    parser.add_argument("--output-dir", default="", help="Output directory override.")
    parser.add_argument("--language", default="", help="Language code for MinerU, default auto.")

    parser.add_argument("--ocr", dest="ocr", action="store_true", help="Force OCR on.")
    parser.add_argument("--no-ocr", dest="ocr", action="store_false", help="Force OCR off.")
    parser.set_defaults(ocr=None)

    parser.add_argument("--poll-interval", type=int, default=0, help="Polling interval in seconds.")
    parser.add_argument("--max-wait", type=int, default=0, help="Max polling wait time in seconds.")
    parser.add_argument("--request-timeout", type=int, default=0, help="Per request timeout in seconds.")
    parser.add_argument("--keep-zip", action="store_true", help="Keep downloaded zip files.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = _load_config(Path(args.config).resolve())

        api_key = args.api_key.strip() or str(config.get("api_key") or "").strip()
        if not api_key or api_key.startswith("YOUR_"):
            raise MineruError("Missing api_key. Set it in mineru_config.json or use --api-key.")

        base_url = str(config.get("base_url") or "https://mineru.net").strip()
        language = args.language.strip() or str(config.get("language") or "auto").strip()
        enable_formula = _parse_bool(config.get("enable_formula"), True)

        is_ocr = args.ocr
        if is_ocr is None:
            is_ocr = _parse_bool(config.get("is_ocr"), True)

        poll_interval = args.poll_interval or int(config.get("poll_interval_seconds") or 3)
        max_wait = args.max_wait or int(config.get("max_wait_seconds") or 1800)
        request_timeout = args.request_timeout or int(config.get("request_timeout_seconds") or 60)

        default_formats = config.get("default_formats") or ["markdown", "json"]
        format_input = args.formats.strip() or ",".join(str(item) for item in default_formats)
        formats = _normalize_formats(format_input)

        inputs = _collect_input_files(args.inputs)
        output_dir_raw = args.output_dir.strip() or str(config.get("output_dir") or "./output")
        output_root = Path(output_dir_raw).resolve()
        output_root.mkdir(parents=True, exist_ok=True)

        print(f"Input files: {len(inputs)}")
        print(f"Formats: {', '.join(sorted(formats))}")

        batch = _create_batch(
            base_url=base_url,
            api_key=api_key,
            files=inputs,
            formats=formats,
            is_ocr=bool(is_ocr),
            language=language,
            enable_formula=enable_formula,
            timeout=request_timeout,
        )

        batch_id = batch["batch_id"]
        print(f"Batch created: {batch_id}")

        _upload_files(
            files=inputs,
            request_files=batch["request_files"],
            url_map=batch["url_map"],
            timeout=request_timeout,
        )

        started = time.time()
        results: List[Dict[str, Any]] = []

        while True:
            fetched = _fetch_batch_results(
                base_url=base_url,
                api_key=api_key,
                batch_id=batch_id,
                timeout=request_timeout,
            )
            results = fetched.get("extract_result") or []
            done_count = sum(str(item.get("state", "")).lower() == "done" for item in results)
            failed_count = sum(str(item.get("state", "")).lower() == "failed" for item in results)
            print(f"Polling batch {batch_id}: done={done_count}, failed={failed_count}, total={len(results)}")

            if _is_all_terminal(results, len(inputs)):
                break

            if time.time() - started > max_wait:
                raise MineruError(f"Timed out while waiting for batch {batch_id}.")

            time.sleep(max(1, poll_interval))

        batch_output_dir = output_root / batch_id
        batch_output_dir.mkdir(parents=True, exist_ok=True)

        generated = _download_and_extract(
            results=results,
            output_dir=batch_output_dir,
            formats=formats,
            timeout=request_timeout,
            keep_zip=args.keep_zip,
        )

        print(f"Batch complete: {batch_id}")
        if generated:
            print("Generated files:")
            for item in generated:
                print(f"- {item}")
        else:
            print("No matching output files were downloaded. Check task states or requested formats.")

        failed_items = [item for item in results if str(item.get("state", "")).lower() == "failed"]
        if failed_items:
            print("Some files failed:")
            for item in failed_items:
                print(f"- {item.get('file_name')} ({item.get('err_msg')})")

        return 0
    except MineruError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())











