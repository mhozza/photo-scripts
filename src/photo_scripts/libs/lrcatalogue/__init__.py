import sqlite3
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

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

    def combine_with(self, other: 'PhotoMetadata') -> 'PhotoMetadata':
        if self.picked == Picked.PICKED or other.picked == Picked.PICKED:
            new_picked = Picked.PICKED
        elif self.picked == Picked.UNPICKED or other.picked == Picked.UNPICKED:
            new_picked = Picked.UNPICKED
        else:
            new_picked = Picked.REJECTED
        
        new_rating = None
        if self.rating is not None or other.rating is not None:
            new_rating = max(self.rating or 0, other.rating or 0)

        return PhotoMetadata(picked=new_picked, rating=new_rating)

@dataclass
class Photo:
    id: int
    path: Path
    metadata: PhotoMetadata

def _get_root_folders(conn: sqlite3.Connection) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, absolutePath FROM AgLibraryRootFolder")
    return {row[0]: Path(row[1]) for row in cursor.fetchall()}

def _get_folders(conn: sqlite3.Connection, root_folders: dict) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT id_local, pathFromRoot, rootFolder FROM AgLibraryFolder")
    return {row[0]: root_folders[row[2]] / row[1] for row in cursor.fetchall()}

def _get_photos_metadata(conn: sqlite3.Connection) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT rootFile, pick, rating FROM Adobe_images")
    metadata = {}
    for row in cursor.fetchall():
        photo_id, pick, rating = row
        new_metadata = PhotoMetadata(Picked.from_int(pick), rating)
        if photo_id in metadata:
            metadata[photo_id] = metadata[photo_id].combine_with(new_metadata)
        else:
            metadata[photo_id] = new_metadata
    return metadata

def get_all_photos(lrcat_path: Path) -> list:
    all_photos = []
    try:
        with sqlite3.connect(lrcat_path) as conn:
            root_folders = _get_root_folders(conn)
            folders = _get_folders(conn, root_folders)
            metadata = _get_photos_metadata(conn)
            
            cursor = conn.cursor()
            cursor.execute("SELECT id_local, folder, originalFilename FROM AgLibraryFile")
            for row in cursor.fetchall():
                photo_id, folder_id, filename = row
                if photo_id in metadata:
                    photo_metadata = metadata[photo_id]
                    path = folders[folder_id] / filename
                    all_photos.append(Photo(photo_id, path, photo_metadata))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    return all_photos

def get_unpicked_photos(lrcat_path: Path) -> list:
    all_photos = get_all_photos(lrcat_path)
    unpicked_photos = []
    for photo in all_photos:
        if photo.metadata.picked != Picked.PICKED and photo.metadata.rating is None:
            unpicked_photos.append(photo)
    return unpicked_photos