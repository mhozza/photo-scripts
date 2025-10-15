import sqlite3
from pathlib import Path
import sys
from photo_scripts.libs import lrcatalogue

ENHANCED_SUFFIX = "-Enhanced-NR.dng"

def register_subcommand(subparsers):
    parser = subparsers.add_parser("sync-edits", help="Sync edit data between raw and enhanced photos.")
    parser.add_argument("lrcat_path", type=Path, help="Path to the .lrcat file.")
    parser.add_argument("--direction", default="enhanced-to-raw", choices=["enhanced-to-raw", "raw-to-enhanced"], help="Sync direction.")
    parser.add_argument("--create-virtual-copies", action="store_true", default=False, help="Create new virtual copies for the edits.")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually modify the database.")
    parser.set_defaults(func=sync_edits)

def find_pairs(all_photos):
    photos_by_path = {photo.path: photo for photo in all_photos}
    pairs = []
    for photo in all_photos:
        if photo.path.suffix.lower() in ['.cr2', '.cr3']:
            enhanced_dng_path = photo.path.with_name(f"{photo.path.stem}{ENHANCED_SUFFIX}")
            if enhanced_dng_path in photos_by_path:
                raw_photo = photo
                enhanced_photo = photos_by_path[enhanced_dng_path]
                pairs.append((raw_photo, enhanced_photo))
    return pairs

def sync_metadata(conn, source_image_id, dest_image_id, dry_run):
    source_metadata = lrcatalogue.get_metadata(conn, source_image_id)
    if not source_metadata:
        print(f"Warning: Could not find metadata for source photo with image id {source_image_id}", file=sys.stderr)
        return

    print(f"  - Syncing metadata: pick={source_metadata.picked.value}, rating={source_metadata.rating}, colorLabels='{source_metadata.colorLabels}'")

    if not dry_run:
        lrcatalogue.update_metadata_from_source(conn, source_image_id, dest_image_id)

def sync_edits(args):
    lrcat_path = args.lrcat_path
    dry_run = args.dry_run
    direction = args.direction
    create_virtual_copies = args.create_virtual_copies

    all_photos = lrcatalogue.get_all_photos(lrcat_path)
    pairs = find_pairs(all_photos)

    print(f"Found {len(pairs)} pairs of raw and enhanced photos.")

    if dry_run:
        print("Dry run mode. No changes will be made.")

    processed_count = 0
    skipped_count = 0

    conn = sqlite3.connect(lrcat_path)
    try:
        with conn:
            for raw_photo, enhanced_photo in pairs:
                if direction == "enhanced-to-raw":
                    source_photo = enhanced_photo
                    dest_photo = raw_photo
                else:
                    source_photo = raw_photo
                    dest_photo = enhanced_photo

                print(f"Processing pair: {raw_photo.path} and {enhanced_photo.path}")

                if not create_virtual_copies:
                    # Safe mode
                    if len(dest_photo.virtual_copies) > 1:
                        print(f"Warning: Destination photo {dest_photo.path} has multiple virtual copies. Skipping in safe mode.", file=sys.stderr)
                        skipped_count += 1
                        continue
                    if lrcatalogue.has_develop_adjustments(conn, dest_photo.virtual_copies[0].image_id):
                        print(f"Warning: Destination photo {dest_photo.path} has already been edited. Skipping in safe mode.", file=sys.stderr)
                        skipped_count += 1
                        continue
                    
                    processed_count += 1
                    source_master_vc = source_photo.virtual_copies[0]
                    dest_master_vc = dest_photo.virtual_copies[0]
                    print(f"Syncing {source_photo.path} -> {dest_photo.path}")
                    sync_metadata(conn, source_master_vc.image_id, dest_master_vc.image_id, dry_run)
                    if not dry_run:
                        lrcatalogue.update_develop_settings(conn, source_master_vc.image_id, dest_master_vc.image_id)
                else:
                    # Advanced mode
                    processed_count += 1
                    for source_vc in source_photo.virtual_copies:
                        source_develop_settings_text = lrcatalogue.get_develop_settings_text(conn, source_vc.image_id)
                        if not source_develop_settings_text:
                            print(f"    Warning: Could not find develop settings for source virtual copy with image id {source_vc.image_id}. Skipping.", file=sys.stderr)
                            continue

                        # Deduplication check
                        found_duplicate = False
                        for dest_vc in dest_photo.virtual_copies:
                            dest_develop_settings_text = lrcatalogue.get_develop_settings_text(conn, dest_vc.image_id)
                            if dest_develop_settings_text == source_develop_settings_text:
                                print(f"    Info: Virtual copy with the same develop settings already exists for {dest_photo.path}. Skipping.", file=sys.stderr)
                                found_duplicate = True
                                break
                        
                        if found_duplicate:
                            continue

                        print(f"  - Creating virtual copy for {dest_photo.path}")
                        if not dry_run:
                            new_vc = lrcatalogue.create_virtual_copy(conn, dest_photo, source_vc.metadata.picked, source_vc.metadata.rating)
                            lrcatalogue.copy_develop_settings(conn, source_vc.image_id, new_vc.image_id)

    finally:
        conn.close()

    print(f"\nProcessed {processed_count} pairs.")
    print(f"Skipped {skipped_count} pairs.")
