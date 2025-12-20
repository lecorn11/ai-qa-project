from ai_qa.infrastructure.database import get_db, User

db = next(get_db())

count = db.query(User).count()
print(f"用户数量:{count}")

db.close()
print("数据库连接成功，用户表查询正常。")