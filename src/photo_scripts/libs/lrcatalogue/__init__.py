import sqlite3
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

class Picked(Enum):
    UNPICKED = 0
    PICKED = 1
    REJECTED = 2

    @classmethod
    def from_int(cls, picked: int):
        try:
            return cls(picked)
        except ValueError:
            return cls.UNPICKED

@dataclass
class PhotoMetadata:
    picked: Picked
    rating: int = None

@dataclass
class VirtualCopy:
    image_id: int # Adobe_images.id_local
    metadata: PhotoMetadata

@dataclass
class Photo:
    id: int # AgLibraryFile.id_local
    path: Path
    virtual_copies: list[VirtualCopy] = field(default_factory=list)

def _get_root_folders(conn: sqlite3.Connection) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, absolutePath FROM AgLibraryRootFolder")
    return {row[0]: Path(row[1]) for row in cursor.fetchall()}

def _get_folders(conn: sqlite3.Connection, root_folders: dict) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, pathFromRoot, rootFolder FROM AgLibraryFolder")
    return {row[0]: root_folders[row[2]] / row[1] for row in cursor.fetchall()}

def _get_photos_data(conn: sqlite3.Connection) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, rootFile, pick, rating FROM Adobe_images")
    photos_data = {}
    for image_id, rootFile, pick, rating in cursor.fetchall():
        if rootFile not in photos_data:
            photos_data[rootFile] = []
        photos_data[rootFile].append(VirtualCopy(
            image_id=image_id,
            metadata=PhotoMetadata(Picked.from_int(pick), rating)
        ))
    return photos_data

def get_all_photos(lrcat_path: Path) -> list:
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

def get_unpicked_photos(lrcat_path: Path) -> list:
    all_photos = get_all_photos(lrcat_path)
    unpicked_photos = []
    for photo in all_photos:
        # A photo is unpicked if all its virtual copies are unpicked
        if all(vc.metadata.picked != Picked.PICKED for vc in photo.virtual_copies) and all(vc.metadata.rating is None for vc in photo.virtual_copies):
            unpicked_photos.append(photo)
    return unpicked_photos