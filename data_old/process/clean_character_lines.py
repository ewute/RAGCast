"""Clean character_lines.csv by removing character classes with few examples.

This script reads a CSV with columns including at least: saga,song,character,lines
It filters out any rows whose character occurs fewer than `min_count` times
and writes a cleaned CSV. By default `min_count=3` (so characters with 1 or 2
lines are removed).

Usage:
    python clean_character_lines.py 
    python clean_character_lines.py --input path/to/character_lines.csv --output path/to/clean.csv --min-count 3
"""

from pathlib import Path
import argparse
import pandas as pd
import logging


def parse_args():
    p = argparse.ArgumentParser(description='Filter character_lines.csv to remove characters with few examples')
    p.add_argument('--input', '-i', type=str, default=str(Path(__file__).resolve().parents[1] / 'data' / 'process' / 'character_lines.csv'),
                   help='Input CSV path (default: project/data/process/character_lines.csv)')
    p.add_argument('--output', '-o', type=str, default=str(Path(__file__).resolve().parents[1] / 'data' / 'clean' / 'character_lines_clean.csv'),
                   help='Output CSV path for cleaned data')
    p.add_argument('--min-count', '-m', type=int, default=3,
                   help='Minimum number of rows a character must have to be kept (default: 3). Characters with fewer than this are removed.')
    p.add_argument('--save-removed', type=str, default=None,
                   help='Optional path to save removed rows (CSV)')
    p.add_argument('--verbose', '-v', action='store_true')
    return p.parse_args()


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(message)s')


def clean_character_lines(input_path: str, output_path: str, min_count: int, removed_out: str = None):
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f'Input file not found: {input_path}')

    # Read CSV
    df = pd.read_csv(input_path)
    logging.info('Read %d rows from %s', len(df), input_path)

    # Expect a 'character' column; try to find one if not present
    if 'character' not in df.columns:
        # look for likely candidates
        candidates = [c for c in df.columns if c.lower() in ('character', 'speaker', 'char')]
        if candidates:
            char_col = candidates[0]
            logging.info('Using column "%s" as character column', char_col)
            df = df.rename(columns={char_col: 'character'})
        else:
            raise RuntimeError('No "character" column found in input CSV')

    # Count per character
    counts = df['character'].value_counts()
    logging.info('Found %d unique characters', len(counts))

    # Characters to keep: with count >= min_count
    keep_chars = counts[counts >= min_count].index.tolist()
    removed_chars = counts[counts < min_count]

    logging.info('Keeping %d characters with >= %d examples; removing %d characters with < %d examples',
                 len(keep_chars), min_count, len(removed_chars), min_count)

    df_clean = df[df['character'].isin(keep_chars)].reset_index(drop=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    logging.info('Wrote cleaned dataset with %d rows to %s', len(df_clean), output_path)

    if removed_out:
        removed_path = Path(removed_out)
        removed_path.parent.mkdir(parents=True, exist_ok=True)
        # Save removed rows for inspection
        df_removed = df[~df['character'].isin(keep_chars)].reset_index(drop=True)
        df_removed.to_csv(removed_path, index=False)
        logging.info('Wrote removed rows (%d) to %s', len(df_removed), removed_path)

    # Return summary info
    return {
        'original_rows': len(df),
        'clean_rows': len(df_clean),
        'unique_characters_original': len(counts),
        'unique_characters_kept': len(keep_chars),
        'removed_characters_count': len(removed_chars),
        'removed_characters_sample': removed_chars.head(20).to_dict()
    }


def main():
    args = parse_args()
    setup_logging(args.verbose)

    summary = clean_character_lines(args.input, args.output, args.min_count, args.save_removed)

    logging.info('Summary: %s', summary)
    print('\nSummary:')
    for k, v in summary.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
