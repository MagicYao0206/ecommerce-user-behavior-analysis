# 导入需要的工具库
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text

# -------------------------- 关键配置 --------------------------
MYSQL_CONFIG = {
    "user": "root",          # MySQL用户名
    "password": "1111",    # MySQL密码
    "host": "localhost",     # 本地地址
    "port": 3306,            # MySQL端口
    "database": "ecommerce_analysis"  # 数据库名
}

# 连接MySQL
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset=utf8mb4"
)

# -------------------------- 数据清洗核心函数 --------------------------
def clean_data():
    # 1. 加载数据（只取前100万行，避免内存溢出）
    # 替换成你的数据路径，比如D:\ecommerce-user-behavior-analysis\data\user_behavior.csv
    file_path = "F:\\ecommerce-user-behavior-analysis\\data\\user_behavior.csv"
    df = pd.read_csv(
        file_path,
        nrows=1000000,  # 仅取前100万行
        names=["user_id", "item_id", "category_id", "behavior_type", "timestamp"],  # 给列命名
        encoding="utf8"
    )

    # 打印原始数据信息
    print("=== 原始数据 ===")
    print(f"数据行数：{df.shape[0]}")  # 输出：1000000
    print(f"前5行数据：\n{df.head()}")

    # 2. 清洗数据
    # 2.1 把时间戳转成可读时间（如1511548800 → 2017-11-25 00:00:00）
    df["time"] = pd.to_datetime(df["timestamp"], unit="s")
    df["date"] = df["time"].dt.date  # 提取日期（2017-11-25）
    df["hour"] = df["time"].dt.hour   # 提取小时（0-23）

    # 2.2 过滤异常时间（只保留2017-11-25至2017-12-03的数据）
    start_date = datetime(2017, 11, 25).date()
    end_date = datetime(2017, 12, 3).date()
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    # 2.3 过滤无效数据（比如用户ID为空的行）
    df = df[(df["user_id"].notnull()) & (df["item_id"].notnull())]

    # 2.4 把行为类型转成中文（pv→浏览，方便分析）
    behavior_mapping = {"pv": "浏览", "fav": "收藏", "cart": "加购", "buy": "购买"}
    df["behavior_name"] = df["behavior_type"].map(behavior_mapping)

    # 打印清洗后的数据信息
    print("\n=== 清洗后数据 ===")
    print(f"数据行数：{df.shape[0]}")  # 大概98万行（过滤了异常数据）
    print(f"行为类型分布：\n{df['behavior_name'].value_counts()}")

    # 3. 导入MySQL（分块导入，避免卡死）
    print("\n=== 开始导入MySQL ===")
    df.to_sql(
        name="user_behavior",  # 导入到user_behavior表
        con=engine,            # 连接MySQL的引擎
        if_exists="replace",   # 如果表有数据，覆盖
        index=False,           # 不导入索引列
        chunksize=10000        # 每次导入1万行，分100次完成
    )
    print("✅ user_behavior表导入完成！")

    # 4. 生成用户汇总数据（统计每个用户的浏览/购买次数）
    summary_sql = """
    INSERT INTO user_summary (user_id, pv_count, fav_count, cart_count, buy_count, last_buy_time)
    SELECT 
        user_id,
        SUM(CASE WHEN behavior_type='pv' THEN 1 ELSE 0 END) AS pv_count,
        SUM(CASE WHEN behavior_type='fav' THEN 1 ELSE 0 END) AS fav_count,
        SUM(CASE WHEN behavior_type='cart' THEN 1 ELSE 0 END) AS cart_count,
        SUM(CASE WHEN behavior_type='buy' THEN 1 ELSE 0 END) AS buy_count,
        MAX(CASE WHEN behavior_type='buy' THEN time ELSE NULL END) AS last_buy_time
    FROM user_behavior
    GROUP BY user_id
    ON DUPLICATE KEY UPDATE
        pv_count=VALUES(pv_count),
        fav_count=VALUES(fav_count),
        cart_count=VALUES(cart_count),
        buy_count=VALUES(buy_count),
        last_buy_time=VALUES(last_buy_time);
    """
    # 执行SQL语句
    with engine.connect() as conn:
        conn.execute(text(summary_sql))
        conn.commit()
    print("✅ user_summary表导入完成！")

# 运行函数
if __name__ == "__main__":
    clean_data()