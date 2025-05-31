from fastapi import FastAPI, HTTPException, Depends, Header, Form, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import sqlite3
from pathlib import Path

app = FastAPI(title="User Verification API")

# Database path (adjust as needed)
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "Verifier_bot/verifier_data.db"
API_KEY = "4cb0385f-25c7-4103-9df8-7783c09fd87d"

if not DATABASE_PATH.exists():
    raise FileNotFoundError(f"Database file not found at {DATABASE_PATH}")

# Pydantic model for user data (response)
class User(BaseModel):
    user_id: str
    start_time: Optional[str] = None
    username: Optional[str] = None
    collect_fio: Optional[str] = None
    platform_login: Optional[str] = None
    api_key: Optional[str] = None
    workgroup_name: Optional[str] = None
    phone_number: Optional[str] = None
    passport_photo_1: Optional[str] = None
    passport_photo_2: Optional[str] = None
    video_file: Optional[str] = None

# Pydantic model for updating user data (request)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    collect_fio: Optional[str] = None
    platform_login: Optional[str] = None
    api_key: Optional[str] = None
    workgroup_name: Optional[str] = None
    phone_number: Optional[str] = None
    passport_photo_1: Optional[str] = None
    passport_photo_2: Optional[str] = None
    video_file: Optional[str] = None

def get_db_connection():
    """Create and return a SQLite database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def verify_api_key(api_key: str = Header(..., alias="Authorization", convert_underscores=False)):
    if not api_key or not api_key.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="API key not found.")

    api_key_value = api_key.replace("Bearer ", "").strip()

    if api_key_value != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


FULL_PATH_OF_VERIFIER_BOT = Path(__file__).resolve().parent.parent / "Verifier_bot/"
@app.get("/users/", response_model=list[User], dependencies=[Depends(verify_api_key)])
async def list_users():
    """Retrieve a list of all users from the user_verification table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_verification")
        users = cursor.fetchall()
        conn.close()

        # Convert database rows to Pydantic models
        user_list = [
            User(
                user_id=row["user_id"],
                start_time=row["start_time"],
                username=row["username"],
                collect_fio=row["collect_fio"],
                platform_login=row["platform_login"],
                api_key=row["api_key"],
                workgroup_name=row["workgroup_name"],
                phone_number=row["phone_number"],
                passport_photo_1=str(FULL_PATH_OF_VERIFIER_BOT / row["passport_photo_1"]),
                passport_photo_2=str(FULL_PATH_OF_VERIFIER_BOT / row["passport_photo_2"]),
                video_file=str(FULL_PATH_OF_VERIFIER_BOT / row["video_file"])
            )
            for row in users
        ]
        return user_list
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.put("/users/{user_id}", response_model=User, dependencies=[Depends(verify_api_key)])
async def update_user(
    user_id: str,
    username: Optional[str] = Form(None),
    collect_fio: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    passport_photo_1: Optional[UploadFile] = File(None),
    passport_photo_2: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверка на существование пользователя
        cursor.execute("SELECT * FROM user_verification WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")

        update_data = {}

        if username is not None:
            update_data["username"] = username
        if collect_fio is not None:
            update_data["collect_fio"] = collect_fio
        if phone_number is not None:
            update_data["phone_number"] = phone_number

        import os

        if passport_photo_1 is not None:
            old_path = user["passport_photo_1"] if user["passport_photo_1"] is not None else None
            if old_path and os.path.exists(old_path):
                os.remove(old_path)
                print(f"Deleted old file: {old_path}")

            folder = os.path.dirname(old_path) if old_path else f"uploads/{user_id}"
            os.makedirs(folder, exist_ok=True)

            file_path = os.path.join(folder, passport_photo_1.filename)
            with open(file_path, "wb") as buffer:
                content = await passport_photo_1.read()  # Читаем содержимое
                buffer.write(content)
                print(f"Saved new file to: {file_path}, size: {len(content)} bytes")
            update_data["passport_photo_1"] = file_path

        if passport_photo_2 is not None:
            old_path = user["passport_photo_2"] if user["passport_photo_2"] is not None else None
            if old_path and os.path.exists(old_path):
                os.remove(old_path)
                print(f"Deleted old file: {old_path}")

            folder = os.path.dirname(old_path) if old_path else f"uploads/{user_id}"
            os.makedirs(folder, exist_ok=True)

            file_path = os.path.join(folder, passport_photo_2.filename)
            with open(file_path, "wb") as buffer:
                content = await passport_photo_2.read()
                buffer.write(content)
                print(f"Saved new file to: {file_path}, size: {len(content)} bytes")
            update_data["passport_photo_2"] = file_path

        if video_file is not None:
            old_path = user["video_file"] if user["video_file"] is not None else None
            if old_path and os.path.exists(old_path):
                os.remove(old_path)
                print(f"Deleted old file: {old_path}")

            folder = os.path.dirname(old_path) if old_path else f"uploads/{user_id}"
            os.makedirs(folder, exist_ok=True)

            file_path = os.path.join(folder, video_file.filename)
            with open(file_path, "wb") as buffer:
                content = await video_file.read()
                buffer.write(content)
                print(f"Saved new file to: {file_path}, size: {len(content)} bytes")
            update_data["video_file"] = file_path

        if not update_data:
            conn.close()
            raise HTTPException(status_code=400, detail="No fields provided for update")

        # Динамическое обновление полей
        set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
        values = list(update_data.values()) + [user_id]
        query = f"UPDATE user_verification SET {set_clause} WHERE user_id = ?"
        cursor.execute(query, values)
        conn.commit()

        # Получение обновленного пользователя
        cursor.execute("SELECT * FROM user_verification WHERE user_id = ?", (user_id,))
        updated_user = cursor.fetchone()
        conn.close()

        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated user")

        return User(
            user_id=updated_user["user_id"],
            start_time=updated_user["start_time"],
            username=updated_user["username"],
            collect_fio=updated_user["collect_fio"],
            platform_login=updated_user["platform_login"],
            api_key=updated_user["api_key"],
            workgroup_name=updated_user["workgroup_name"],
            phone_number=updated_user["phone_number"],
            passport_photo_1=str(FULL_PATH_OF_VERIFIER_BOT / updated_user["passport_photo_1"]),
            passport_photo_2=str(FULL_PATH_OF_VERIFIER_BOT / updated_user["passport_photo_2"]),
            video_file=str(FULL_PATH_OF_VERIFIER_BOT / updated_user["video_file"])
        )

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)