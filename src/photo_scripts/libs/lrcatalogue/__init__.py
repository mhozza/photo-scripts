import sqlite3
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
import uuid
import sys

class Picked(Enum):
    """Enum for the pick status of a photo."""
    UNPICKED = 0
    PICKED = 1
    REJECTED = 2

    @classmethod
    def from_int(cls, picked: int):
        """Creates a Picked enum from an integer."""
        try:
            return cls(picked)
        except ValueError:
            return cls.UNPICKED

@dataclass
class PhotoMetadata:
    """Dataclass for storing the metadata of a photo."""
    picked: Picked
    rating: int = None
    colorLabels: str = None

@dataclass
class VirtualCopy:
    """Dataclass for storing the data of a virtual copy."""
    image_id: int # Adobe_images.id_local
    metadata: PhotoMetadata

@dataclass
class Photo:
    """Dataclass for storing the data of a photo, including its virtual copies."""
    id: int # AgLibraryFile.id_local
    path: Path
    virtual_copies: list[VirtualCopy] = field(default_factory=list)

def _get_root_folders(conn: sqlite3.Connection) -> dict:
    """Gets all root folders from the Lightroom catalog."""
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, absolutePath FROM AgLibraryRootFolder")
    return {row[0]: Path(row[1]) for row in cursor.fetchall()}

def _get_folders(conn: sqlite3.Connection, root_folders: dict) -> dict:
    """Gets all folders from the Lightroom catalog."""
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, pathFromRoot, rootFolder FROM AgLibraryFolder")
    return {row[0]: root_folders[row[2]] / row[1] for row in cursor.fetchall()}

def _get_photos_data(conn: sqlite3.Connection) -> dict:
    """Gets the metadata for all photos and their virtual copies."""
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, rootFile, pick, rating, colorLabels FROM Adobe_images")
    photos_data = {}
    for image_id, rootFile, pick, rating, colorLabels in cursor.fetchall():
        if rootFile not in photos_data:
            photos_data[rootFile] = []
        photos_data[rootFile].append(VirtualCopy(
            image_id=image_id,
            metadata=PhotoMetadata(Picked.from_int(pick), rating, colorLabels)
        ))
    return photos_data

def get_all_photos(lrcat_path: Path) -> list[Photo]:
    """Gets all photos from the Lightroom catalog, including their virtual copies."""
    all_photos = []
    try:
        with sqlite3.connect(lrcat_path) as conn:
            root_folders = _get_root_folders(conn)
            folders = _get_folders(conn, root_folders)
            photos_data = _get_photos_data(conn)
            
            cursor = conn.cursor()
            cursor.execute("SELECT id_local, folder, originalFilename FROM AgLibraryFile")
            for photo_id, folder_id, filename in cursor.fetchall():
                if photo_id in photos_data:
                    path = folders[folder_id] / filename
                    all_photos.append(Photo(photo_id, path, photos_data[photo_id]))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    return all_photos

def get_unpicked_photos(lrcat_path: Path) -> list[Photo]:
    """Gets all unpicked photos from the Lightroom catalog."""
    all_photos = get_all_photos(lrcat_path)
    unpicked_photos = []
    for photo in all_photos:
        if all(vc.metadata.picked != Picked.PICKED for vc in photo.virtual_copies) and all(vc.metadata.rating is None for vc in photo.virtual_copies):
            unpicked_photos.append(photo)
    return unpicked_photos

def has_develop_adjustments(conn: sqlite3.Connection, image_id: int) -> bool:
    """Checks if a photo has any develop adjustments."""
    cursor = conn.cursor()
    cursor.execute("SELECT hasDevelopAdjustments FROM Adobe_imageDevelopSettings WHERE image = ?", (image_id,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else False

def get_develop_settings_text(conn: sqlite3.Connection, image_id: int) -> str:
    """Gets the develop settings text for a photo."""
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM Adobe_imageDevelopSettings WHERE image = ?", (image_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_metadata(conn: sqlite3.Connection, image_id: int) -> PhotoMetadata:
    """Gets the metadata for a photo."""
    cursor = conn.cursor()
    cursor.execute("SELECT pick, rating, colorLabels FROM Adobe_images WHERE id_local = ?", (image_id,))
    row = cursor.fetchone()
    if not row:
        return None
    
    pick, rating, colorLabels = row
    return PhotoMetadata(picked=Picked.from_int(pick), rating=rating, colorLabels=colorLabels)

def update_metadata_from_source(conn: sqlite3.Connection, source_image_id: int, dest_image_id: int):
    """Copies the metadata from a source image to a destination image by updating the existing record."""
    source_metadata = get_metadata(conn, source_image_id)
    if not source_metadata:
        return

    cursor = conn.cursor()
    cursor.execute("UPDATE Adobe_images SET pick = ?, rating = ?, colorLabels = ? WHERE id_local = ?",
                   (source_metadata.picked.value, source_metadata.rating, source_metadata.colorLabels, dest_image_id))

def copy_develop_settings(conn: sqlite3.Connection, source_image_id: int, dest_image_id: int):
    """Copies the develop settings from a source image to a new develop settings record for the destination image."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Adobe_imageDevelopSettings WHERE image = ?", (source_image_id,))
    source_settings_row = cursor.fetchone()
    if not source_settings_row:
        return

    column_names = [d[0] for d in cursor.description]
    source_settings = dict(zip(column_names, source_settings_row))

    source_settings['image'] = dest_image_id
    source_settings['hasDevelopAdjustments'] = 1
    if 'id_local' in source_settings:
        del source_settings['id_local']

    columns = ", ".join(source_settings.keys())
    placeholders = ", ".join([":" + k for k in source_settings.keys()])
    sql = f"INSERT INTO Adobe_imageDevelopSettings ({columns}) VALUES ({placeholders})"
    cursor.execute(sql, source_settings)

def update_develop_settings(conn: sqlite3.Connection, source_image_id: int, dest_image_id: int):
    """Updates an existing develop settings record for a destination image from a source image."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Adobe_imageDevelopSettings WHERE image = ?", (source_image_id,))
    source_settings_row = cursor.fetchone()
    if not source_settings_row:
        return

    column_names = [d[0] for d in cursor.description]
    source_settings = dict(zip(column_names, source_settings_row))

    columns_to_update = [c for c in column_names if c not in ['id_local', 'image']]
    
    update_values = [source_settings[c] for c in columns_to_update]
    update_values.append(dest_image_id)

    set_clause = ", ".join([f"{c} = ?" for c in columns_to_update])
    
    sql = f"UPDATE Adobe_imageDevelopSettings SET {set_clause} WHERE image = ?"
    cursor.execute(sql, tuple(update_values))

def create_virtual_copy(conn: sqlite3.Connection, dest_photo: Photo, pick: Picked = None, rating: int = None) -> VirtualCopy:
    """Creates a new virtual copy for a photo."""
    cursor = conn.cursor()
    
    new_image_id_global = str(uuid.uuid4()).upper()
    master_image_id = dest_photo.virtual_copies[0].image_id
    
    cursor.execute("SELECT * FROM Adobe_images WHERE id_local = ?", (master_image_id,))
    master_image_row = cursor.fetchone()
    column_names = [d[0] for d in cursor.description]
    master_image_data = dict(zip(column_names, master_image_row))

    master_image_data['id_global'] = new_image_id_global
    master_image_data['masterImage'] = master_image_id
    
    if pick is not None:
        master_image_data['pick'] = pick.value
    if rating is not None:
        master_image_data['rating'] = rating

    if 'id_local' in master_image_data:
        del master_image_data['id_local']

    columns = ", ".join(master_image_data.keys())
    placeholders = ", ".join([":" + k for k in master_image_data.keys()])
    sql = f"INSERT INTO Adobe_images ({columns}) VALUES ({placeholders})"
    cursor.execute(sql, master_image_data)
    new_image_id = cursor.lastrowid

    new_metadata = PhotoMetadata(
        picked=Picked.from_int(master_image_data['pick']),
        rating=master_image_data['rating'],
        colorLabels=master_image_data['colorLabels']
    )
    new_vc = VirtualCopy(image_id=new_image_id, metadata=new_metadata)
    
    dest_photo.virtual_copies.append(new_vc)

    return new_vc