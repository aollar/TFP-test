#!/usr/bin/env python3
"""
Generate a gallery README for the TFP/ folder.

Scans TFP/ recursively for all files, groups them by filename prefix,
and generates TFP/README.md with:
- Embedded previews for images (png, jpg, jpeg, gif, webp, svg)
- Raw GitHub download links for documents and other files

Usage:
    python tools/make_tfp_readme_gallery.py
"""

import re
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict

# GitHub repository configuration
GITHUB_OWNER = "aollar"
GITHUB_REPO = "TFP-test"
GITHUB_BRANCH = "main"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/refs/heads/{GITHUB_BRANCH}/TFP"


# File type categories
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt'}
SPREADSHEET_EXTENSIONS = {'.xls', '.xlsx', '.csv', '.ods'}
PRESENTATION_EXTENSIONS = {'.ppt', '.pptx', '.odp'}
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml'}
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz', '.rar', '.7z'}

# Emoji icons for file types
FILE_ICONS = {
    'image': '🖼️',
    'document': '📄',
    'spreadsheet': '📊',
    'presentation': '📽️',
    'code': '💻',
    'archive': '📦',
    'other': '📎',
}


def get_file_type(extension: str) -> str:
    """Determine the file type category from extension."""
    ext = extension.lower()
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in DOCUMENT_EXTENSIONS:
        return 'document'
    elif ext in SPREADSHEET_EXTENSIONS:
        return 'spreadsheet'
    elif ext in PRESENTATION_EXTENSIONS:
        return 'presentation'
    elif ext in CODE_EXTENSIONS:
        return 'code'
    elif ext in ARCHIVE_EXTENSIONS:
        return 'archive'
    return 'other'


def url_encode_path(path: str) -> str:
    """URL-encode a path, handling spaces and special characters."""
    parts = path.split('/')
    encoded_parts = [quote(part, safe='') for part in parts]
    return '/'.join(encoded_parts)


def extract_prefix(filename: str) -> str:
    """
    Extract the grouping prefix from a filename.

    Examples:
        "Business-Innovation Q1.png" -> "Business-Innovation"
        "Sperm and Egg Q2.png" -> "Sperm and Egg"
        "random-file.txt" -> "Misc"
    """
    # Remove extension for analysis
    stem = Path(filename).stem

    # Pattern: prefix followed by Q1/Q2/Q3/Q4
    match = re.match(r'^(.+?)\s+Q[1-4]$', stem, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern: prefix followed by "image Q1/Q2/Q3/Q4"
    match = re.match(r'^(.+?)\s+image\s+Q[1-4]$', stem, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return "Misc"


def natural_sort_key(s: str):
    """Sort key for natural (human-friendly) sorting."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]


def make_anchor(title: str) -> str:
    """Create a GitHub-compatible anchor from a title."""
    anchor = title.lower()
    anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
    anchor = re.sub(r'\s+', '-', anchor)
    return anchor


def generate_readme(tfp_dir: Path) -> str:
    """Generate the README.md content."""

    # Find all files recursively (exclude README.md itself and hidden files)
    all_files = sorted(
        [f for f in tfp_dir.rglob('*')
         if f.is_file()
         and f.name != 'README.md'
         and not f.name.startswith('.')],
        key=lambda p: natural_sort_key(p.name)
    )

    if not all_files:
        return "# TFP File Gallery\n\nNo files found.\n"

    # Separate images and other files
    image_files = [f for f in all_files if f.suffix.lower() in IMAGE_EXTENSIONS]
    other_files = [f for f in all_files if f.suffix.lower() not in IMAGE_EXTENSIONS]

    # Group image files by prefix
    image_groups = defaultdict(list)
    for img_path in image_files:
        rel_path = img_path.relative_to(tfp_dir)
        prefix = extract_prefix(img_path.name)
        image_groups[prefix].append(rel_path)

    # Group other files by type
    other_by_type = defaultdict(list)
    for file_path in other_files:
        rel_path = file_path.relative_to(tfp_dir)
        file_type = get_file_type(file_path.suffix)
        other_by_type[file_type].append(rel_path)

    # Sort image groups: named groups first, then Misc
    sorted_image_groups = sorted(
        image_groups.keys(),
        key=lambda x: (x == "Misc", natural_sort_key(x))
    )

    # Build README content
    lines = []

    # Header
    lines.append("# TFP File Gallery")
    lines.append("")
    lines.append("This folder contains TFP (The Fractal Pattern) files organized by category.")
    lines.append("")

    # Stats
    lines.append(f"**Total files:** {len(all_files)} ({len(image_files)} images, {len(other_files)} documents/other)")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")

    if image_files:
        lines.append("### Images")
        for group_name in sorted_image_groups:
            anchor = make_anchor(group_name)
            count = len(image_groups[group_name])
            lines.append(f"- [{group_name}](#{anchor}) ({count} files)")

    if other_files:
        lines.append("")
        lines.append("### Documents & Other Files")
        lines.append(f"- [Documents & Other Files](#documents--other-files-1)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Generate image sections
    for group_name in sorted_image_groups:
        files = image_groups[group_name]

        lines.append(f"## {group_name}")
        lines.append("")

        # Sort files within group naturally
        files = sorted(files, key=lambda p: natural_sort_key(str(p)))

        # Create 2-column table layout
        lines.append("<table>")

        for i in range(0, len(files), 2):
            lines.append("<tr>")

            # First column
            file1 = files[i]
            encoded_path1 = url_encode_path(str(file1))
            display_name1 = file1.stem

            lines.append("<td align=\"center\">")
            lines.append(f"<img src=\"{encoded_path1}\" width=\"520\" alt=\"{display_name1}\"><br>")
            lines.append(f"<b>{display_name1}</b><br>")
            lines.append(f"<a href=\"{encoded_path1}\">Open image</a>")
            lines.append("</td>")

            # Second column (if exists)
            if i + 1 < len(files):
                file2 = files[i + 1]
                encoded_path2 = url_encode_path(str(file2))
                display_name2 = file2.stem

                lines.append("<td align=\"center\">")
                lines.append(f"<img src=\"{encoded_path2}\" width=\"520\" alt=\"{display_name2}\"><br>")
                lines.append(f"<b>{display_name2}</b><br>")
                lines.append(f"<a href=\"{encoded_path2}\">Open image</a>")
                lines.append("</td>")
            else:
                lines.append("<td></td>")

            lines.append("</tr>")

        lines.append("</table>")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Generate documents/other files section
    if other_files:
        lines.append("## Documents & Other Files")
        lines.append("")
        lines.append("| File | Type | Description |")
        lines.append("|------|------|-------------|")

        for file_path in sorted(other_files, key=lambda p: natural_sort_key(str(p))):
            rel_path = file_path.relative_to(tfp_dir)
            encoded_filename = url_encode_path(str(rel_path))
            raw_url = f"{RAW_BASE_URL}/{encoded_filename}"
            file_type = get_file_type(file_path.suffix)
            icon = FILE_ICONS.get(file_type, FILE_ICONS['other'])
            ext = file_path.suffix.upper().lstrip('.')

            lines.append(f"| {icon} [{rel_path.name}]({raw_url}) | {ext} | {rel_path.stem} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Footer
    lines.append("*This gallery was auto-generated by `tools/make_tfp_readme_gallery.py`*")
    lines.append("")

    return '\n'.join(lines)


def main():
    # Determine paths
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    tfp_dir = repo_root / "TFP"
    readme_path = tfp_dir / "README.md"

    if not tfp_dir.exists():
        print(f"Error: TFP directory not found at {tfp_dir}")
        return 1

    # Generate README content
    content = generate_readme(tfp_dir)

    # Write README
    readme_path.write_text(content, encoding='utf-8')
    print(f"Generated: {readme_path}")

    # Report stats
    all_files = [f for f in tfp_dir.rglob('*') if f.is_file() and f.name != 'README.md']
    image_count = len([f for f in all_files if f.suffix.lower() in IMAGE_EXTENSIONS])
    other_count = len(all_files) - image_count
    print(f"Found {len(all_files)} files ({image_count} images, {other_count} documents/other)")

    return 0


if __name__ == "__main__":
    exit(main())
